import numpy as np


def calculate_kurtosis(matrix):
    """
    计算输入矩阵（二维或任意维）数据的 Pearson 峰度。
    参数: matrix (np.ndarray): 输入的矩阵
    返回: float: 数据的峰度值 (κ)
    """
    # 将矩阵展平为一维分布，以便进行整体统计分析
    data = matrix.flatten()

    # 计算均值 μ 和标准差 σ
    mu = np.mean(data)
    sigma = np.std(data)

    # 防止标准差为 0 导致除零错误
    if sigma == 0:
        return 0.0

    # 计算关于均值的四阶矩 μ4 = E[(x - μ)^4]
    mu4 = np.mean((data - mu) ** 4)

    # 根据公式计算峰度 κ = μ4 / σ^4
    kurtosis = mu4 / (sigma ** 4)

    return kurtosis


# 使用示例
X = np.random.normal(0, 1, (1024, 1024))
print(f"正态分布的峰度为: {calculate_kurtosis(X):.4f}")