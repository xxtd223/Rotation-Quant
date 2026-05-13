import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import torch
from safetensors.torch import load_file as st_load_file


class DataGenerator:
    def __init__(self, m: int, n: int):
        """
        初始化数据生成器
        :param m: rows
        :param n: columns
        """
        self.m = m
        self.n = n
        self._llama_weights_cache = {}  # 缓存 LLM 权重的字典，避免重复加载模型
        self._llama_activations_cache = {}  # 缓存激活值字典
        self.save_dir = "weights_cache"
        self.local_model_dir = "weights"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def _load_llama_weights(self):
        """
        从 safetensors 文件提取模型权重
        """
        weight_types = ['Llama_WQ', 'Llama_WK', 'Llama_WV', 'Llama_WO']

        if all(os.path.exists(os.path.join(self.save_dir, f"{name}.npy")) for name in weight_types):
            for name in weight_types:
                if name not in self._llama_weights_cache:
                    self._llama_weights_cache[name] = np.load(os.path.join(self.save_dir, f"{name}.npy"))
            return

        if not self.local_model_dir:
            raise ValueError("本地模型文件缺失。")

        shard_path = os.path.join(self.local_model_dir, "model-00001-of-00002.safetensors")
        print(f"正在读取权重: {shard_path}")

        try:
            state_dict = st_load_file(shard_path)
            mapping = {
                'Llama_WQ': 'model.layers.0.self_attn.q_proj.weight',
                'Llama_WK': 'model.layers.0.self_attn.k_proj.weight',
                'Llama_WV': 'model.layers.0.self_attn.v_proj.weight',
                'Llama_WO': 'model.layers.0.self_attn.o_proj.weight'
            }

            for name, key in mapping.items():
                if key in state_dict:
                    val_tensor = state_dict[key]
                    # BFloat16 转换为 Float32
                    arr = val_tensor.to(dtype=torch.float32).cpu().numpy()
                    np.save(os.path.join(self.save_dir, f"{name}.npy"), arr)
                    self._llama_weights_cache[name] = arr
                    print(f"已缓存 {name} 到本地缓存")
                else:
                    print(f"在文件中未找到 {key}，请检查分片是否正确。")

            del state_dict
        except Exception as e:
            raise RuntimeError(f"读取模型失败: {e}")

    def _load_llama_activations(self):
        """
        从 .pt 文件加载推理时的激活值
        """
        activation_types = ['Llama_XQ', 'Llama_XK', 'Llama_XV', 'Llama_XO']

        # 如果所有激活值都已在缓存中，直接返回
        if all(name in self._llama_activations_cache for name in activation_types):
            return

        activation_dir = "activations_output"
        if not os.path.exists(activation_dir):
            raise FileNotFoundError(f"找不到激活值目录: {activation_dir}，请先运行数据抓取脚本。")

        print(f"正在从 {activation_dir} 加载激活值...")

        for name in activation_types:
            file_path = os.path.join(activation_dir, f"{name}.pt")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"缺失激活值文件: {file_path}")

            try:
                tensor = torch.load(file_path, map_location='cpu')
                # 转为 numpy 数组 Float32
                arr = tensor.detach().to(dtype=torch.float32).numpy()

                self._llama_activations_cache[name] = arr
                print(f"已成功加载激活值缓存: {name}, 形状: {arr.shape}")
                del tensor
            except Exception as e:
                raise RuntimeError(f"加载激活值 {name} 失败: {e}")

    def generate(self, dist_type: str, scale_factor: float = 20.0, num_outliers: int = None, a: float = None):
        """
        生成指定分布的数据
        :param num_outliers: 指定离群值数量
        :param dist_type: 分布类型 key
        :param scale_factor: 极端值放大的倍数 (默认为20倍)
        :return: m*n 的 numpy 矩阵
        """
        # 基础配置
        base_loc = 0
        base_scale = 1
        if a is None:
            a = scale_factor

        # 大模型真实数据抽取
        if dist_type in ['Llama_WQ', 'Llama_WK', 'Llama_WV', 'Llama_WO']:
            self._load_llama_weights()
            full_matrix = self._llama_weights_cache[dist_type]

            max_rows, max_cols = full_matrix.shape
            if self.m > max_rows or self.n > max_cols:
                raise ValueError(
                    f"请求的矩阵块大小 ({self.m}x{self.n}) 超出了真实权重矩阵的最大尺寸 ({max_rows}x{max_cols})！")

            # 随机生成起始行和起始列
            start_row = np.random.randint(0, max_rows - self.m + 1)
            start_col = np.random.randint(0, max_cols - self.n + 1)

            # 抽取随机块
            block_data = full_matrix[start_row:start_row + self.m, start_col:start_col + self.n].copy()
            return block_data

        if dist_type in ['Llama_XQ', 'Llama_XK', 'Llama_XV', 'Llama_XO']:
            # 假设你已经有一个加载本地 .pt 文件到缓存的方法
            self._load_llama_activations()
            full_matrix = self._llama_activations_cache[dist_type]

            # 如果是 [Batch, Seq, Dim]，通常取第一个 Batch 并转为 2D: [Seq, Dim]
            if full_matrix.ndim == 3:
                full_matrix = full_matrix[0]

            max_rows, max_cols = full_matrix.shape

            # 尺寸安全检查
            if self.m > max_rows or self.n > max_cols:
                raise ValueError(
                    f"请求的激活值块大小 ({self.m}x{self.n}) 超出了矩阵实际尺寸 ({max_rows}x{max_cols})！"
                    f"提示：请增加推理时的输入文本长度 (Sequence Length) 以增加行数。")

            # 随机生成起始位置
            start_row = np.random.randint(0, max_rows - self.m + 1)
            start_col = np.random.randint(0, max_cols - self.n + 1)

            # 抽取随机块
            block_data = full_matrix[start_row:start_row + self.m, start_col:start_col + self.n].copy()
            return block_data.T

        # 正态分布
        if dist_type == 'normal':
            data = np.random.normal(loc=base_loc, scale=base_scale, size=(self.m, self.n))

        # 拉普拉斯分布
        elif dist_type == 'laplace':
            data = np.random.laplace(loc=base_loc, scale=base_scale, size=(self.m, self.n))

        # 随机均匀分布
        elif dist_type == 'uniform':
            data = np.random.uniform(low=base_loc - base_scale * 3, high=base_loc + base_scale * 3, size=(self.m, self.n))

        # 针对包含“极端值”的情况，基础数据均使用拉普拉斯分布
        else:
            # 先生成全量的基础小范围拉普拉斯数据
            data = np.random.laplace(loc=base_loc, scale=base_scale, size=(self.m, self.n))

            # 确定异常样本(行)的数量
            outlier_count = 0
            if dist_type == 'one_extreme':
                outlier_count = 1
            elif dist_type == 'half_extreme':
                outlier_count = int(self.m / 2)
            elif dist_type == 'mostly_extreme':
                outlier_count = self.m - 10
            elif dist_type == 'completely_extreme':
                outlier_count = self.m
            elif dist_type == 'custom_extreme':
                # 默认为1，不超过总数 m
                outlier_count = min(num_outliers if num_outliers is not None else 1, self.m)
            else:
                raise ValueError(f"未知的分布类型: {dist_type}")

            if outlier_count > 0:
                # 高效实现：随机选择 outlier_count 个不重复的行索引
                outlier_indices = np.random.choice(self.m, outlier_count, replace=False)

                # 制造离群值：x*a+a
                raw_values = data[outlier_indices]
                outliers = raw_values * a + np.sign(raw_values) * a
                data[outlier_indices] = outliers

        return data

    def visualize(self, data, title="Data Visualization", save_path=None):
        """
        可视化生成的矩阵
        """
        plt.figure(figsize=(10, 5))

        '''
        # 散点图 (展示前两个维度)
        plt.subplot(1, 3, 1)
        if self.n >= 2:
            sns.scatterplot(x=data[:, 0], y=data[:, 1], alpha=0.6, edgecolor=None)
            plt.title("2D Projection (Dim 0 vs Dim 1)")
            plt.xlabel("Dim 0")
            plt.ylabel("Dim 1")
        else:
            plt.plot(data, 'o', alpha=0.6)
            plt.title("1D Scatter")
        '''

        # 直方图 (展示整体数值分布)
        plt.subplot(1, 2, 1)
        sns.histplot(data.flatten(), bins=50, kde=True, color='skyblue')
        plt.title("Value Distribution Histogram")
        # plt.yscale('log')  # 使用对数坐标
        plt.ylabel("Count (Log Scale)")

        # 热力图 (展示矩阵整体结构)
        plt.subplot(1, 2, 2)
        abs_data = np.abs(data)
        sns.heatmap(abs_data,
                    cmap="inferno",  # 色系
                    cbar=True,
                    vmin=np.percentile(abs_data, 5),
                    vmax=np.percentile(abs_data, 95))

        plt.title(f"Abs Matrix Heatmap ({self.m}x{self.n})")
        plt.xlabel("Features (n)")
        plt.ylabel("Samples (m)")

        plt.suptitle(title, fontsize=16)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            plt.close()
        else:
            plt.show()
