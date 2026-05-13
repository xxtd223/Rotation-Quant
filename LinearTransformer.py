import numpy as np


class LinearTransformer:
    def __init__(self):
        pass

    def _is_power_of_two(self, n):
        return (n != 0) and (n & (n - 1) == 0)

    def _get_hadamard_matrix(self, n):
        """
        利用递归/Kronecker积思想生成 n*n 的阿达马矩阵
        """
        if not self._is_power_of_two(n):
            raise ValueError(f"Hadamard变换要求维度n必须是2的幂次方，当前n={n}")

        # 初始 W1 = [1]
        H = np.array([[1]])

        # 迭代生成：每次维度翻倍
        k = 1
        while k < n:
            # 构造 [[H, H], [H, -H]]
            H = np.block([
                [H, H],
                [H, -H]
            ])
            k *= 2

        return H / np.sqrt(n)

    def _get_householder_matrix(self, n, mode='fixed'):
        """
        生成 n*n 的 Householder 矩阵：H = I - 2vv*
        """
        # 构造向量 v
        if mode == 'random':
            # 随机生成
            v = np.random.randn(n, 1)
        elif mode == 'fixed':
            # [-1, 1, ..., 1]
            v = np.ones((n, 1))
            v[0] = -1
        else:
            raise ValueError("Unknown Householder mode")

        # 归一化
        v = v / np.linalg.norm(v)

        # H = I - 2 * v * v.T
        I = np.eye(n)
        H = I - 2 * np.dot(v, v.T)

        return H

    def transform(self, data, method='hadamard', W=None):
        """
        对输入矩阵进行线性变换
        :param data: m*n 的 numpy 矩阵
        :param method: 'hadamard', 'householder_fixed', 'householder_random'， ‘WUSH'
        :return: 变换后的矩阵, 变换矩阵T
        """
        m, n = data.shape
        X = data

        if method == 'hadamard':
            T = self._get_hadamard_matrix(m)

        elif method == 'householder_fixed':
            T = self._get_householder_matrix(m, mode='fixed')

        elif method == 'householder_random':
            T = self._get_householder_matrix(m, mode='random')

        elif method == 'White':
            # 加上微小的 epsilon 扰动防止矩阵不可逆
            eps = 1e-6 * np.eye(m)
            cov_X = X @ X.T + eps

            # 特征值分解 (EVD)
            Lambda, U = np.linalg.eigh(cov_X)
            # Lambda = np.maximum(Lambda, 1e-10) # 防止数值精度导致的微小负数

            Lambda_inv_sqrt = np.diag(Lambda ** (-0.5))

            # T = Lambda^{-1/2} * U^T
            T = Lambda_inv_sqrt @ U.T

        elif method == 'White_W':
            if W is None:
                raise ValueError("方法 'White_W' 要求提供权重矩阵 W")
            eps = 1e-6 * np.eye(m)
            cov_W = W @ W.T + eps  # 权重矩阵
            Lambda, U = np.linalg.eigh(cov_W)
            Lambda_inv_sqrt = np.diag(Lambda ** (-0.5))

            T_temp = Lambda_inv_sqrt @ U.T
            T = np.linalg.inv(T_temp.T)

        elif method == 'WUSH':
            if W is None:
                raise ValueError("方法 'WUSH' 要求提供权重矩阵 W")
            if W.shape[0] != m:
                raise ValueError(f"权重矩阵 W 的行数({W.shape[0]})必须与激活值 X 的行数({m})一致")

            # 计算 X*X^T 和 W*W^T 的 Cholesky 分解
            # 加上微小的 eps 扰动
            eps = 1e-6 * np.eye(m)
            X_prime_L = np.linalg.cholesky(X @ X.T + eps)
            W_prime_L = np.linalg.cholesky(W @ W.T + eps)

            # 对 (W')^T * X' 进行奇异值分解 (SVD)
            # 根据公式：U, S, V = SVD(W_prime_L.T @ X_prime_L)
            U, S, V = np.linalg.svd(W_prime_L.T @ X_prime_L)

            # 获取归一化的 Hadamard 矩阵
            H = self._get_hadamard_matrix(m)

            # 构造变换矩阵 T = H * S^{-1/2} * U^T * W'^T
            S_inv_sqrt = np.diag(S ** (-0.5))
            T = H @ S_inv_sqrt @ U.T @ W_prime_L.T

        elif method == 'WUSH_withoutC':
            if W is None:
                raise ValueError("方法 'WUSH' 要求提供权重矩阵 W")
            if W.shape[0] != m:
                raise ValueError(f"权重矩阵 W 的行数({W.shape[0]})必须与激活值 X 的行数({m})一致")

            # 奇异值分解 (SVD)
            U, S, V = np.linalg.svd(W.T @ X)
            # 取前 m 个成分
            U = U[:, :m]
            S = S[:m]

            # 获取归一化的 Hadamard 矩阵
            H = self._get_hadamard_matrix(m)

            # T = H * S^{-1/2} * U^T * W^T
            S_inv_sqrt = np.diag(S ** (-0.5))
            T = H @ S_inv_sqrt @ U.T @ W.T

        elif method == 'WUS':
            if W is None:
                raise ValueError("方法 'WUS' 要求提供权重矩阵 W")
            if W.shape[0] != m:
                raise ValueError(f"权重矩阵 W 的行数({W.shape[0]})必须与激活值 X 的行数({m})一致")

            eps = 1e-6 * np.eye(m)
            X_prime_L = np.linalg.cholesky(X @ X.T + eps)
            W_prime_L = np.linalg.cholesky(W @ W.T + eps)

            U, S, V = np.linalg.svd(W_prime_L.T @ X_prime_L)

            # T = S^{-1/2} * U^T * W'^T
            S_inv_sqrt = np.diag(S ** (-0.5))
            T = S_inv_sqrt @ U.T @ W_prime_L.T

        elif method == 'SQ':
            if W is None:
                raise ValueError("方法 'SQ' 要求提供权重矩阵 W")

            # 1. 计算协方差矩阵
            # 增加 eps 保证数值稳定性，防止矩阵奇异
            eps_mat = 1e-6 * np.eye(m)
            Cx = X @ X.T + eps_mat
            Cw = W @ W.T + eps_mat

            # 2. 计算 Cx 的平方根及其逆
            # 利用 eigh 处理对称矩阵，比常规 eig 更稳定且快
            Lx, Vx = np.linalg.eigh(Cx)
            Lx = np.maximum(Lx, 1e-9)  # 截断极小特征值
            Cx_sqrt = Vx @ np.diag(np.sqrt(Lx)) @ Vx.T
            Cx_inv_sqrt = Vx @ np.diag(1.0 / np.sqrt(Lx)) @ Vx.T

            # 3. 计算中间对称矩阵 A = Cx^{1/2} @ Cw @ Cx^{1/2}
            A = Cx_sqrt @ Cw @ Cx_sqrt
            La, Va = np.linalg.eigh(A)
            La = np.maximum(La, 1e-9)
            A_sqrt = Va @ np.diag(np.sqrt(La)) @ Va.T

            # 4. 构造目标矩阵 M = Cx^{-1/2} @ A^{1/2} @ Cx^{-1/2}
            M = Cx_inv_sqrt @ A_sqrt @ Cx_inv_sqrt

            # 5. 对 M 进行特征值分解: M = Q @ S @ Q.T
            Lm, Q = np.linalg.eigh(M)
            Lm = np.maximum(Lm, 1e-9)

            # 6. 构造变换矩阵 T = S^{1/2} @ Q^T
            S_pow = np.diag(Lm ** (0.5))
            T = S_pow @ Q.T

        elif method == 'SQH':
            if W is None:
                raise ValueError("方法 'SQH' 要求提供权重矩阵 W")

            eps_mat = 1e-6 * np.eye(m)
            Cx = X @ X.T + eps_mat
            Cw = W @ W.T + eps_mat

            Lx, Vx = np.linalg.eigh(Cx)
            Lx = np.maximum(Lx, 1e-9)  # 截断极小特征值
            Cx_sqrt = Vx @ np.diag(np.sqrt(Lx)) @ Vx.T
            Cx_inv_sqrt = Vx @ np.diag(1.0 / np.sqrt(Lx)) @ Vx.T

            A = Cx_sqrt @ Cw @ Cx_sqrt
            La, Va = np.linalg.eigh(A)
            La = np.maximum(La, 1e-9)
            A_sqrt = Va @ np.diag(np.sqrt(La)) @ Va.T
            M = Cx_inv_sqrt @ A_sqrt @ Cx_inv_sqrt
            Lm, Q = np.linalg.eigh(M)
            Lm = np.maximum(Lm, 1e-9)

            S_pow = np.diag(Lm ** (0.5))
            H = self._get_hadamard_matrix(m)
            T = H @ S_pow @ Q.T

        else:
            raise ValueError(f"不支持的变换类型: {method}")

        # 执行矩阵乘法
        transformed_data = np.dot(T, data)

        return transformed_data, T


