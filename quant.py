import numpy as np


def fake_quant_int4(matrix):
    """
    INT4 块级量化/反量化模拟（按列展开）
    取值范围: [-8, 7]
    假设输入矩阵元素总数是 32 的倍数
    """
    if matrix.size % 32 != 0:
        raise ValueError(f"矩阵总元素个数 ({matrix.size}) 必须是 Block 大小 (32) 的倍数。")

    orig_shape = matrix.shape
    # 按列优先展平
    flattened = matrix.flatten(order='F')
    # 划分为大小为 32 的块
    blocks = flattened.reshape(-1, 32)

    # INT4 的边界定义
    q_min = -8
    q_max = 7

    # 计算缩放因子，根据每一块的最大绝对值
    block_abs_max = np.max(np.abs(blocks), axis=1, keepdims=True)
    block_abs_max[block_abs_max == 0] = 1e-9  # 防止除零
    s_block = block_abs_max / q_max

    # 量化
    q_blocks = np.round(blocks / s_block)
    # 截断超出的部分
    q_blocks = np.clip(q_blocks, q_min, q_max)

    # 反量化
    reconstructed_blocks = q_blocks * s_block

    # 映射回原形状
    return reconstructed_blocks.flatten().reshape(orig_shape, order='F')


def int4_quant_error(W, X, T, T_inv):
    """
    模拟引入变换 T 后的线性层 (Y = W^T * X) INT4 量化误差。
    """
    # 计算精确结果
    Y_exact = W.T @ X

    # 应用变换
    X_prime = T @ X
    W_prime = T_inv.T @ W

    # 模拟量化
    W_prime_quant = fake_quant_int4(W_prime)
    X_prime_quant = fake_quant_int4(X_prime)

    # 推理
    Y_approx = W_prime_quant.T @ X_prime_quant

    # 误差评估
    error_matrix = Y_approx - Y_exact
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae


def fake_quant_mxfp4(matrix):
    """
    底层的 MXFP4 块级量化/反量化模拟（按列展开）
    1S2E1M-8E
    假设输入矩阵元素总数是 32 的倍数
    """
    if matrix.size % 32 != 0:
        raise ValueError(f"矩阵总元素个数 ({matrix.size}) 必须是 Block 大小 (32) 的倍数。")

    orig_shape = matrix.shape

    # 按列优先展平
    flattened = matrix.flatten(order='F')

    # 划分为大小为 32 的块
    blocks = flattened.reshape(-1, 32)

    # FP4 (1S2E1M) 的正数表达域
    fp4_positive_values = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    max_fp4 = np.max(fp4_positive_values)

    # 提取局部块级最大绝对值
    block_max = np.max(np.abs(blocks), axis=1, keepdims=True)
    block_max[block_max == 0] = 1e-9  # 防止除零

    s_block = block_max / max_fp4

    # 模拟 8E 量化缩放因子
    s_block_clipped = np.clip(s_block, 2.0 ** -126, 2.0 ** 127)

    # 转换为 2 的幂次
    e_quant = np.round(np.log2(s_block_clipped))
    s_block_e8 = 2.0 ** e_quant

    scaled_blocks = blocks / s_block_e8

    # 最近邻偶数舍入 (RNE) 映射
    signs = np.sign(scaled_blocks)
    # 截断 (Clip)
    abs_scaled = np.abs(scaled_blocks)
    abs_scaled = np.clip(abs_scaled, 0.0, max_fp4)

    diff = np.abs(abs_scaled[..., np.newaxis] - fp4_positive_values)
    nearest_idx = np.argmin(diff, axis=-1)
    q_blocks = signs * fp4_positive_values[nearest_idx]

    # 反量化还原
    reconstructed_blocks = q_blocks * s_block_e8

    # 将一维结果重新按列优先 (order='F') 映射回原有的二维矩阵形状
    return reconstructed_blocks.flatten().reshape(orig_shape, order='F')


def mxfp4_quant_error(W, X, T, T_inv):
    """
    模拟引入变换 T 后的线性层 (Y = W^T * X) 量化误差。

    参数:
    W (np.ndarray): 权重矩阵，形状为 (D, M)
    X (np.ndarray): 激活矩阵，形状为 (D, N)
    T (np.ndarray): 变换矩阵，形状为 (D, D)

    返回:
    error_matrix (np.ndarray): 线性层输出的量化误差矩阵 (M, N)
    mae (float): 误差矩阵的平均绝对误差
    """
    # 计算理论上的精确前向传播结果 Y = W.T @ X
    Y_exact = W.T @ X

    # 对权重和激活值应用变换
    X_prime = T @ X
    W_prime = T_inv.T @ W

    # 对变换后的 W' 和 X' 进行 MXFP4 模拟量化
    W_prime_quant = fake_quant_mxfp4(W_prime)
    X_prime_quant = fake_quant_mxfp4(X_prime)

    # 执行量化后的矩阵乘法推理
    Y_approx = W_prime_quant.T @ X_prime_quant

    # 评估重构误差
    error_matrix = Y_approx - Y_exact
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae


def fake_quant_nvfp4(matrix):
    """
    底层的 NVFP4 块级量化/反量化模拟（按列展开）
    1S2E1M-1S4E3M
    假设输入矩阵行数是 16 的倍数
    """
    if matrix.size % 16 != 0:
        raise ValueError(f"矩阵总元素个数 ({matrix.size}) 必须是 Block 大小 (16) 的倍数。")

    orig_shape = matrix.shape

    # 按列优先展平
    flattened = matrix.flatten(order='F')

    # 划分为大小为 16 的块
    blocks = flattened.reshape(-1, 16)

    # FP4 (1S2E1M) 的正数表达域
    fp4_positive_values = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    max_fp4 = np.max(fp4_positive_values)

    # 提取局部块级最大绝对值
    block_max = np.max(np.abs(blocks), axis=1, keepdims=True)
    block_max[block_max == 0] = 1e-9  # 防止除零

    s_block = block_max / max_fp4

    # 模拟 E4M3 (1位符号, 4位指数, 3位尾数) 量化
    s_block_clipped = np.clip(s_block, 2.0 ** -9, 448.0)
    # 提取底数 m 和指数 e：s = m * 2^e, 其中 m 在 [0.5, 1) 之间
    m, e = np.frexp(s_block_clipped)
    # 转换为标准的 IEEE 浮点科学计数法格式: 1.m * 2^e'
    m_ieee = m * 2.0
    e_ieee = e - 1
    m_quant = np.round((m_ieee - 1.0) * 8.0) / 8.0
    # 重构 E4M3 精度的缩放因子
    s_block_e4m3 = (1.0 + m_quant) * (2.0 ** e_ieee)

    scaled_blocks = blocks / s_block_e4m3

    # 最近邻偶数舍入 (RNE) 映射
    signs = np.sign(scaled_blocks)
    # 如果量化后的 s_block_e4m3 略小于 s_block，会导致缩放后的最大值超过 6.0，必须进行截断 (Clip)
    abs_scaled = np.abs(scaled_blocks)
    abs_scaled = np.clip(abs_scaled, 0.0, max_fp4)

    diff = np.abs(abs_scaled[..., np.newaxis] - fp4_positive_values)
    nearest_idx = np.argmin(diff, axis=-1)
    q_blocks = signs * fp4_positive_values[nearest_idx]

    # 反量化还原
    reconstructed_blocks = q_blocks * s_block_e4m3

    # 将一维结果重新按列优先 (order='F') 映射回原有的二维矩阵形状
    return reconstructed_blocks.flatten().reshape(orig_shape, order='F')


def nvfp4_quant_error(W, X, T, T_inv):
    """
    模拟引入变换 T 后的线性层 (Y = W^T * X) 量化误差。

    参数:
    W (np.ndarray): 权重矩阵，形状为 (D, M)
    X (np.ndarray): 激活矩阵，形状为 (D, N)
    T (np.ndarray): 变换矩阵，形状为 (D, D)

    返回:
    error_matrix (np.ndarray): 线性层输出的量化误差矩阵 (M, N)
    mae (float): 误差矩阵的平均绝对误差
    """
    # 计算理论上的精确前向传播结果 Y = W.T @ X
    Y_exact = W.T @ X

    # 对权重和激活值应用变换
    X_prime = T @ X
    W_prime = T_inv.T @ W

    # 对变换后的 W' 和 X' 进行 NVFP4 模拟量化
    W_prime_quant = fake_quant_nvfp4(W_prime)
    X_prime_quant = fake_quant_nvfp4(X_prime)

    # 执行量化后的矩阵乘法推理
    Y_approx = W_prime_quant.T @ X_prime_quant

    # 评估重构误差
    error_matrix = Y_approx - Y_exact
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae


def unilateral_nvfp4_quant_error(W, X, T, T_inv):
    """
    单边量化：仅量化权重
    """
    # 计算理论上的精确前向传播结果 Y = W.T @ X
    Y_exact = W.T @ X

    # 对权重和激活值应用变换
    X_prime = T @ X
    W_prime = T_inv.T @ W

    # 对变换后的 W' 进行 NVFP4 模拟量化
    W_prime_quant = fake_quant_nvfp4(W_prime)

    # 执行量化后的矩阵乘法推理
    Y_approx = W_prime_quant.T @ X_prime

    # 评估重构误差
    error_matrix = Y_approx - Y_exact
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae

def single_matrix_nvfp4_quant_error(X, T, T_inv):
    """
    单一矩阵的量化误差
    """
    X_prime = T @ X
    X_prime_quant = fake_quant_nvfp4(X_prime)

    # 执行量化后的矩阵乘法推理
    X_approx = T_inv @ X_prime_quant

    # 评估重构误差
    error_matrix = X_approx - X
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae