import numpy as np


def simulate_nvfp4_vectorized(input_matrix):
    """
    模拟 NVFP4 块级量化（不考虑全局缩放因子）。
    参数:
    input_matrix (np.ndarray): 形状为 (n, 16) 的浮点矩阵，每一列视为一个独立的 Block。
    返回:
    error_matrix (np.ndarray): 量化重构误差矩阵，形状与输入一致。
    mae (float): 平均绝对误差 (Mean Absolute Error)。
    """
    # 1. 定义 FP4 (1S2E1M) 的正数表达域 (不含符号位)
    fp4_positive_values = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    max_fp4 = np.max(fp4_positive_values)

    # 2. 提取块级特征并计算 S_block
    # 按列计算绝对值的最大值
    col_max = np.max(np.abs(input_matrix), axis=0, keepdims=True)

    # 防止除零溢出
    col_max[col_max == 0] = 1.0

    # 将实际动态范围映射到 FP4 的最大表达范围
    s_block = col_max / max_fp4

    # 3. 缩放至 FP4 目标域
    scaled_matrix = input_matrix / s_block

    # 4. 执行最近邻偶数舍入 (RNE) 映射
    signs = np.sign(scaled_matrix)
    abs_scaled = np.abs(scaled_matrix)

    # 计算每个元素与 FP4 标准格点的欧氏距离
    diff = np.abs(abs_scaled[..., np.newaxis] - fp4_positive_values)

    # 沿着最后一个维度寻找最小误差对应的格点索引
    nearest_idx = np.argmin(diff, axis=-1)

    # 组合符号位与量化幅值，完成量化
    q_matrix = signs * fp4_positive_values[nearest_idx]

    # 5. 反量化过程：恢复至原始数值量级
    reconstructed_matrix = q_matrix * s_block

    # 6. 计算重构误差与统计量
    error_matrix = reconstructed_matrix - input_matrix
    mae = np.mean(np.abs(error_matrix))

    return error_matrix, mae


# ================= 测试用例 =================
n = 16
X = np.random.uniform(-10, 10, size=(n, 16))

# 执行量化模拟
E, mae = simulate_nvfp4_vectorized(X)

print("输入矩阵:\n", X)
print("误差矩阵:\n", E)
print(f"整体平均绝对误差 (MAE): {mae:.4f}")