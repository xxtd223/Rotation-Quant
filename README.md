# Rotation Quantization Exp

研究旋转变换（Hadamard / WUSH / LQH 等）对 MXFP4 / NVFP4 量化误差和激活值分布的影响，在 Llama 真实权重与多种模拟激活分布上进行系统性对比实验。

## 实验内容

**实验一：模拟激活值量化误差对比**
遍历 8 种激活分布 × 4 种 Llama 权重 × 8 种旋转方法，以 NVFP4 量化 MAE 为指标，重复 n 次取平均。

**实验二：真实激活值量化误差**
使用 Llama Q/K/V/O 真实权重与激活值配对，对每种旋转方法重复随机抽样 n 次求平均 MAE。

**实验三：峰度分析**
针对 Llama_WQ 场景，统计各旋转方法对权重矩阵和激活矩阵峰度的影响，输出变换前后峰度及变化百分比，探究峰度与量化误差的相关性。

## 核心模块

| 文件 | 功能                           |
|------|------------------------------|
| `DataGenerator.py` | 生成模拟激活分布及加载真实 Llama 权重/激活    |
| `LinearTransformer.py` | 实现各旋转变换（Hadamard、LQH、WUSH 等） |
| `quant.py` | NVFP4 block-wise 量化及误差计算     |
| `kurtosis.py` | 峰度计算工具                       |
| `exp_fig.py` | 实验结果可视化                      |

---

# Rotation Quantization Demo

可视化 Demo，直观展示旋转变换（Hadamard / WUSH / LQH）对 FP4 量化的影响。

## 项目结构

```
rotation-demo/
├── src/
│   ├── components/
│   │   ├── Feature1/   # 激活值分布对比（旋转前后直方图）
│   │   ├── Feature2/   # 量化误差热力图（NVFP4 block-wise）
│   │   ├── Feature3/   # 性能指标：Speedup、VRAM、Perplexity
│   │   └── Feature4/   # 硬件仪表盘（压缩比、峰值加速比）
│   └── composables/    # 数据生成、旋转变换、量化逻辑
└── package.json
```

## 启动 Demo

```bash
cd rotation-demo
npm install      
npm run dev      # 默认 http://localhost:5173
```

## 功能说明

| Tab | 内容                                                                                   |
|-----|--------------------------------------------------------------------------------------|
| Feature 1 | 对比原始激活值分布与旋转后分布，支持切换分布类型和旋转方法                                                        |
| Feature 2 | 可视化 NVFP4 量化误差热力图，对比 None / Hadamard / LQH 等旋转效果                                     |
| Feature 3 | 展示 Llama-3.2-3B 和 Qwen3-8B 在 MXFP4 / NVFP4 下的 Speedup、VRAM 占用和 WikiText-2 Perplexity |
| Feature 4 | 动态仪表盘，展示内存压缩比和峰值加速比等关键指标                                                             |
