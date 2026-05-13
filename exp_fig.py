import matplotlib.pyplot as plt
import numpy as np

# ================= 配置宋体、五号(10.5pt)、加粗 =================
plt.rcParams['font.sans-serif'] = ['SimSun']
plt.rcParams['axes.unicode_minus'] = False

CHINESE_FONT = {'family': 'SimSun', 'size': 10.5, 'weight': 'bold'}
# =============================================================

# Data (保持不变)
formats = ['MXFP4', 'NVFP4']
methods = ['None', '+ Hadamard', '+ LQH']

data_static = {
    'Llama-3.2-3B': [[26.56, 27.30, 27.30], [28.12, 28.50, 28.50]],
    'Qwen3-8B': [[26.56, 27.08, 27.08], [28.20, 28.46, 28.46]]
}
data_peak = {
    'Llama-3.2-3B': [[26.56, 27.17, 27.17], [28.12, 28.43, 28.43]],
    'Qwen3-8B': [[26.56, 27.04, 27.04], [28.12, 28.36, 28.36]]
}
data_speedup = {
    'Llama-3.2-3B': [[6.77, 6.00, 5.89], [6.27, 5.67, 5.58]],
    'Qwen3-8B': [[6.66, 6.09, 6.01], [6.24, 5.84, 5.77]]
}

colors = ['#4F9DA3', '#FFC000', '#C00000']


def plot_model_metrics(model_name, filename):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5))
    fig.subplots_adjust(wspace=0.2)
    fig.suptitle(model_name, fontsize=14, fontweight='bold', y=1.02)

    metrics_data = [data_static, data_peak, data_speedup]
    ylabels = ["静态显存占用率 (%)", "峰值显存占用率 (%)", "加速比 vs. FP16"]
    baselines = [None, None, 1.0]

    x = np.arange(len(formats))

    bar_width = 0.2  # 单个柱子的宽度
    gap = 0.05  # 柱子之间的微小间隔
    step = bar_width + gap  # 步长 = 宽度 + 间隔
    # -----------------------

    for i, (data, ylabel, baseline) in enumerate(zip(metrics_data, ylabels, baselines)):
        ax = axes[i]

        for j, method in enumerate(methods):
            values = [data[model_name][k][j] for k in range(len(formats))]
            # 使用 step 代替原先的 width 来计算偏移
            offset = (j - 1) * step

            ax.bar(x + offset, values, bar_width,  # 这里的宽度依然是单根柱子的宽度
                   label=method if i == 0 else "",
                   color=colors[j],
                   edgecolor='#000000',
                   linewidth=2,
                   zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(formats, fontdict={'size': 10.5})
        ax.set_ylabel(ylabel, fontdict=CHINESE_FONT)
        ax.yaxis.grid(True, linestyle='-', alpha=0.5, zorder=0)

        if baseline is not None:
            ax.axhline(y=baseline, color='black', linestyle='--', linewidth=1, zorder=4)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3,
               bbox_to_anchor=(0.5, -0.08),
               prop={'family': 'SimSun', 'size': 10.5, 'weight': 'bold'},
               frameon=False)

    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()


plot_model_metrics('Llama-3.2-3B', 'llama_metrics.png')
plot_model_metrics('Qwen3-8B', 'qwen_metrics.png')
