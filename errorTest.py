import random

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from safetensors.torch import load_file
import torch
import quant


def load_real_weight(
        path="weights/model-00001-of-00002.safetensors",
        max_rows=2048,
        max_cols=2048
):
    """
    从 safetensors 中读取真实权重子矩阵
    """

    state_dict = load_file(path)

    print("===== Searching weight tensor =====")

    for name, tensor in state_dict.items():
        if tensor.ndim == 2 and "weight" in name:
            print(f"\nUsing tensor: {name}")
            print(f"Original shape: {tuple(tensor.shape)}")

            data = tensor.detach().cpu().float().numpy()

            orig_rows, orig_cols = data.shape

            # 确定最终要截取的子矩阵大小
            target_rows = min(orig_rows, max_rows)
            target_cols = min(orig_cols, max_cols)

            # 计算随机起始位置的最大边界
            max_start_row = orig_rows - target_rows
            max_start_col = orig_cols - target_cols

            # 生成随机的起始索引
            start_row = random.randint(0, max_start_row)
            start_col = random.randint(0, max_start_col)

            print(f"Random slice starting at: row {start_row}, col {start_col}")

            # 随机节选子矩阵
            data = data[start_row: start_row + target_rows,
                   start_col: start_col + target_cols]

            print(f"Sub-matrix shape: {data.shape}")

            # 保证元素数量是 32 的倍数
            total = data.size
            valid_size = (total // 32) * 32

            if valid_size != total:
                print(f"Trim total elements: {total} -> {valid_size}")

                # 按列优先展平并截断
                flat = data.flatten(order='F')[:valid_size]

                # reshape 回二维
                data = flat.reshape(target_rows, 32)

            return data

    raise ValueError("未找到合适的二维 weight tensor")


def load_real_activation(
        path="activations_output/Llama_XQ.pt",
        max_rows=2048,
        max_cols=1024
):
    """
    从 .pt 文件中读取真实激活值，并随机截取一个可控大小的子矩阵
    """

    obj = torch.load(path, map_location="cpu")

    print("===== Loading activation tensor =====")
    print(f"Loaded type: {type(obj)}")

    # 1) 直接就是 Tensor
    if isinstance(obj, torch.Tensor):
        tensor = obj

    # 2) 是 dict，尝试找第一个 tensor
    elif isinstance(obj, dict):
        tensor = None
        print("Dict keys:", list(obj.keys())[:20])

        for k, v in obj.items():
            if isinstance(v, torch.Tensor):
                tensor = v
                print(f"Using key: {k}")
                break

        if tensor is None:
            raise ValueError("pt 文件是 dict，但没有找到 Tensor。")

    # 3) 是 list / tuple，尝试找第一个 tensor
    elif isinstance(obj, (list, tuple)):
        tensor = None
        for i, v in enumerate(obj):
            if isinstance(v, torch.Tensor):
                tensor = v
                print(f"Using index: {i}")
                break

        if tensor is None:
            raise ValueError("pt 文件是 list/tuple，但没有找到 Tensor。")

    else:
        raise TypeError(f"不支持的 .pt 内容类型: {type(obj)}")

    print(f"Original shape: {tuple(tensor.shape)}")

    data = tensor.detach().cpu().float().numpy()

    # 如果是高维激活 (例如 [batch, seq_len, hidden_dim])，先压成二维
    if data.ndim > 2:
        data = data.reshape(-1, data.shape[-1])
        print(f"Flattened to 2D shape: {data.shape}")

    orig_rows, orig_cols = data.shape

    # 确定最终要截取的子矩阵大小
    target_rows = min(orig_rows, max_rows)
    target_cols = min(orig_cols, max_cols)

    # 计算随机起始位置的最大边界
    max_start_row = orig_rows - target_rows
    max_start_col = orig_cols - target_cols

    # 生成随机的起始索引
    start_row = random.randint(0, max_start_row)
    start_col = random.randint(0, max_start_col)

    print(f"Random slice starting at: row {start_row}, col {start_col}")

    # 随机节选子矩阵
    data = data[start_row : start_row + target_rows,
                start_col : start_col + target_cols]

    print(f"Sub-matrix shape: {data.shape}")

    # 保证元素数量是 32 的倍数，以适配 Block 级量化
    total = data.size
    valid_size = (total // 32) * 32

    if valid_size != total:
        print(f"Trim total elements: {total} -> {valid_size}")
        flat = data.flatten(order='F')[:valid_size]
        data = flat.reshape(-1, 32)

    return data


def verify_quantization(matrix_size=(1024, 1024)):
    # 生成测试数据
    #log_min, log_max = -3, 1
    #magnitudes = 10 ** np.random.uniform(log_min, log_max, size=matrix_size)
    #signs = np.random.choice([-1, 1], size=matrix_size)
    #data = magnitudes * signs

    # 读取真实模型权重
    data = load_real_activation()

    # 量化
    quantized_data = quant.fake_quant_nvfp4(data)

    x = data.flatten()
    x_hat = quantized_data.flatten()

    # -----------------------------
    # 左图：绝对误差分析
    # -----------------------------
    alpha = np.abs(x)

    # 绝对误差（用于左图）
    epsilon = np.abs(x_hat - x)
    eps_offset = 1e-15

    # 过滤掉 log 空间非法值
    valid_mask = (
            (alpha > 0)
            & (epsilon > 0)
            & np.isfinite(alpha)
            & np.isfinite(epsilon)
    )
    alpha_valid = alpha[valid_mask]
    epsilon_valid = epsilon[valid_mask]

    log_alpha = np.log10(alpha_valid)
    log_epsilon = np.log10(epsilon_valid + eps_offset)

    corr, _ = pearsonr(log_alpha, log_epsilon)

    print(f"Valid samples for log-analysis: {len(alpha_valid)} / {len(alpha)}")

    # -----------------------------
    # 右图：验证 E[η] = 0
    # -----------------------------
    # 带符号误差（核心修改）
    delta = x_hat - x

    # 带符号相对误差
    eta_signed = delta / (x + 1e-12)

    # 验证期望
    eta_mean = np.mean(eta_signed)

    print(f"E[eta] = {eta_mean:.8e}")

    # -----------------------------
    # 绘图
    # -----------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # ===== 左图 =====
    hb = ax1.hexbin(
        alpha_valid,
        epsilon_valid + eps_offset,
        gridsize=70,
        cmap='Blues',
        bins='log',
        xscale='log',
        yscale='log',
        edgecolors='none',
        mincnt=1
    )

    cb = fig.colorbar(hb, ax=ax1)
    cb.set_label(r'$\log_{10}(\mathrm{Count})$', rotation=270, labelpad=15)

    alpha_nonzero = alpha[alpha > 0]
    log_min = np.floor(np.log10(np.min(alpha_nonzero)))
    log_max = np.ceil(np.log10(np.max(alpha_nonzero)))

    ref_x = np.logspace(log_min, log_max, 100)
    ax1.plot(
        ref_x,
        ref_x,
        color='gray',
        linestyle=':',
        alpha=0.6,
        label=r'Underflow Limit ($\epsilon = \alpha$)'
    )

    ax1.text(
        0.05,
        0.92,
        f'Log-Space Corr: {corr:.4f}',
        transform=ax1.transAxes,
        fontsize=12,
        fontweight='bold',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )

    ax1.set_xlabel(r'Magnitude ($\alpha$) [Log Scale]')
    ax1.set_ylabel(r'Absolute Error ($\epsilon$) [Log Scale]')
    ax1.set_title('NVFP4: Error Correlation Analysis')
    ax1.legend(loc='lower right')
    ax1.grid(True, which="both", ls="-", alpha=0.1)

    # ===== 右图 =====
    ax2.hist(
        eta_signed,
        bins=200,
        edgecolor='white',
        alpha=0.8
    )

    ax2.axvline(
        0.0,
        linestyle='--',
        label=rf'$E[\eta] \approx {eta_mean:.2e}$'
    )

    ax2.set_title(r'Distribution of Signed Relative Error ($\eta$)')
    ax2.set_xlabel(r'$\eta = (\hat{x} - x)/x$')
    ax2.set_ylabel('Frequency')
    ax2.legend()

    plt.tight_layout()
    plt.show()

    return corr, eta_mean


verify_quantization()