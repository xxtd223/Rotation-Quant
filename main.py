import math
import pandas as pd
from DataGenerator import DataGenerator
from LinearTransformer import LinearTransformer
import numpy as np
import os
import quant
import kurtosis



group_sizes = [16]  # 仿射变换分组大小

# 类型列表
Xscenarios = [
    ('uniform', 'Uniform Distribution'),
    ('normal', 'Normal Distribution'),
    ('laplace', 'Laplace Distribution'),
    ('one_extreme', 'Single Extreme Outlier (1 vs Rest)'),
    ('custom_extreme', 'Few Extreme Outlier (10% vs Rest)'),
    ('half_extreme', 'Half Extreme Outliers (m/2)'),
    ('mostly_extreme', 'Mostly Extreme Outliers (m * 90%)'),
    ('completely_extreme', 'Completely Extreme Outliers (m)'),
]
Wscenarios = [
    ('Llama_WQ', 'Llama_W_Q'),
    ('Llama_WK', 'Llama_W_K'),
    ('Llama_WV', 'Llama_W_V'),
    ('Llama_WO', 'Llama_W_O'),
]
real_data_pairs = [
    ('Llama_WQ', 'Llama_XQ', 'Q_Projection'),
    ('Llama_WK', 'Llama_XK', 'K_Projection'),
    ('Llama_WV', 'Llama_XV', 'V_Projection'),
    ('Llama_WO', 'Llama_XO', 'O_Projection'),
]
transform_methods = ['None', 'hadamard', 'householder_random', 'White', 'SQ', 'SQH', 'WUS', 'WUSH']

# 保存路径
#os.makedirs("results/plots", exist_ok=True)
os.makedirs("results/plots/weights", exist_ok=True)
os.makedirs("results/plots/activations", exist_ok=True)

A = 10  # 离群值放大系数
n = 10  # 重复次数
transformer = LinearTransformer()
results = []
experiment_id = 1

M = N = D = 256
I = np.identity(D)

# 根据当前尺寸，重新初始化生成器
Wgenerator = DataGenerator(D, M)
Xgenerator = DataGenerator(D, N)


'''
# 这是模拟激活值的实验循环
print(f"开始运行实验，共 {len(group_sizes)} * {len(Wscenarios)} * {len(Xscenarios)} * {len(transform_methods)} 种配置...")

# 第一层：遍历矩阵尺寸 (Group Size)
for gs in group_sizes:
    print(f"\n>>> 正在测试分组大小 gs={gs} <<<")
    if D % gs != 0:
        raise ValueError(f"矩阵维度 {D} 必须能被分组大小 {gs} 整除。")

    # 第二层：遍历权重类型
    for w_key, w_name in Wscenarios:
        print(f"  - 提取权重: {w_name}")
        W = Wgenerator.generate(w_key)

        # 第三层：遍历激活值分布
        for x_key, x_name in Xscenarios:
            # 初始化误差累加器
            mae_accumulators = {method: 0.0 for method in transform_methods}

            # 运行 n 次重复实验以求平均
            for i in range(n):
                # 生成当前的激活矩阵 X
                if x_key == 'custom_extreme':
                    X = Xgenerator.generate(x_key, scale_factor=A, num_outliers=10)
                else:
                    X = Xgenerator.generate(x_key, scale_factor=A)

                # 第四层：遍历所有变换方法
                for method in transform_methods:
                    # 2. 执行仿射变换
                    if method == 'None':
                        trans_X, T_full, T_inv_full = X, I, I
                    else:
                        T_full = np.zeros((D, D))
                        T_inv_full = np.zeros((D, D))
                        trans_X = np.zeros_like(X)
                        # 按 gs 分块处理
                        for g_start in range(0, D, gs):
                            g_end = g_start + gs
                            X_group = X[g_start:g_end, :]
                            W_group = W[g_start:g_end, :]
                            if method in ['WUSH', 'WUS', 'WUSH_withoutC', 'SQ', 'SQH']:
                                trans_X_g, T_g = transformer.transform(X_group, method=method, W=W_group)
                            else:
                                trans_X_g, T_g = transformer.transform(X_group, method=method)

                            # 在分组中求变换矩阵的逆
                            T_g_inv = np.linalg.inv(T_g)

                            # 将分组变换结果拼接到大矩阵中
                            trans_X[g_start:g_end, :] = trans_X_g
                            T_full[g_start:g_end, g_start:g_end] = T_g
                            T_inv_full[g_start:g_end, g_start:g_end] = T_g_inv

                    # 3. 保存可视化图（仅第一次）
                    if i == 0:
                        plot_filename = f"{w_name}_{x_key}_{method}_GS{gs}.png"
                        plot_path = os.path.join("results", "plots", plot_filename)
                        Xgenerator.visualize(trans_X, title=f"{w_name} + {x_name} + {method} (GS={gs})", save_path=plot_path)

                    # 4. 计算量化误差
                    E, mae = nvfp4_quant_error(W, X, T_full, T_inv_full)
                    mae_accumulators[method] += mae

            # 5. 计算 n 次重复的平均误差，并录入结果表
            for method in transform_methods:
                avg_mae = (mae_accumulators[method] / (n * math.sqrt(D))) * 100

                print(f"矩阵大小：{gs}，[{w_name} + {x_name} + {method}] 平均绝对误差: {avg_mae:.4f} (单位：10^-2)")

                results.append({
                    "编号": experiment_id,
                    "矩阵大小 (Group Size)": gs,
                    "权重类型": w_name,
                    "激活分布": x_name,
                    "仿射变换": method,
                    "平均误差 (10^-2)": round(avg_mae, 4),
                    "可视化图路径": f"plots/{w_name}_{x_key}_{method}_GS{gs}.png"
                })
                experiment_id += 1
            print("-" * 50)

# --- 4. 导出为 Excel 供数据透视表使用 ---
df = pd.DataFrame(results)
excel_path = "results/full_results.xlsx"
df.to_excel(excel_path, index=False)

print(f"\n实验完成！结果已保存至 {excel_path}。")
'''

'''
# 这是真实激活值的实验循环（n次求平均值版）
print(f"开始真实数据实验，共 {len(real_data_pairs)} 个场景 * {len(transform_methods)} 种变换...")
print(f"开始计算平均误差实验，n={n}...")

# 第一层：遍历分组大小
for gs in group_sizes:
    print(f"\n>>> 正在测试分组大小 gs={gs} <<<")

    # 第二层：遍历真实数据配对 (Q/K/V/O)
    for w_key, x_key, scene_name in real_data_pairs:
        print(f"  - 正在计算 {scene_name} 的平均误差...")

        # 初始化误差累加器
        mae_accumulators = {method: 0.0 for method in transform_methods}

        # 第三层：运行 n 次随机抽取实验
        for i in range(n):
            W = Wgenerator.generate(w_key)
            X = Xgenerator.generate(x_key)

            # 在第一次迭代时，保存原始权重的可视化图
            if i == 0:
                w_orig_path = os.path.join("results/plots/weights", f"Original_W_{scene_name}_GS{gs}.png")
                Wgenerator.visualize(W, title=f"Original W: {scene_name}", save_path=w_orig_path)

            # 第四层：遍历所有变换方法
            for method in transform_methods:
                if method == 'None':
                    t_X, t_W, T_full, T_inv_full = X, W, I, I
                else:
                    T_full = np.zeros((D, D))
                    T_inv_full = np.zeros((D, D))
                    t_X = np.zeros_like(X)
                    t_W = np.zeros_like(W)

                    for g_start in range(0, D, gs):
                        g_end = g_start + gs
                        X_g, W_g = X[g_start:g_end, :], W[g_start:g_end, :]

                        if method in ['WUSH', 'WUS', 'SQ', 'SQH']:
                            tx_g, T_g = transformer.transform(X_g, method=method, W=W_g)
                        else:
                            tx_g, T_g = transformer.transform(X_g, method=method)

                        T_g_inv = np.linalg.inv(T_g)
                        tw_g = T_g_inv.T @ W_g

                        t_X[g_start:g_end, :] = tx_g
                        t_W[g_start:g_end, :] = tw_g
                        T_full[g_start:g_end, g_start:g_end] = T_g
                        T_inv_full[g_start:g_end, g_start:g_end] = T_g_inv

                # 计算量化误差 (统一为 10^-2 单位)
                _, mae = quant.nvfp4_quant_error(W, X, T_full, T_inv_full)
                scaled_mae = mae * 100

                # 累加本次迭代的误差
                mae_accumulators[method] += scaled_mae

                # 在第一次迭代时，保存变换后的激活值与权重的可视化图
                if i == 0:
                    t_x_path = os.path.join("results/plots/activations", f"Act_{scene_name}_{method}_GS{gs}.png")
                    Xgenerator.visualize(t_X, title=f"Transformed X: {method}", save_path=t_x_path)

                    if method != 'None':
                        t_w_path = os.path.join("results/plots/weights",
                                                f"Transformed_W_{scene_name}_{method}_GS{gs}.png")
                        Wgenerator.visualize(t_W, title=f"Transformed W: {method}", save_path=t_w_path)

        # --- 第五步：计算平均值并输出成绩单 ---
        print("  === 本场景 n 次平均误差成绩单 (MAE 10^-2) ===")

        for method in transform_methods:
            avg_mae = mae_accumulators[method] / n
            print(f"    - {method:<18}: {avg_mae:.4f}")

            # 录入结果表
            results.append({
                "场景": scene_name,
                "分组大小": gs,
                "仿射变换": method,
                "平均误差 (10^-2)": round(avg_mae, 4)
            })

        print("-" * 50)

# 导出 Excel
df = pd.DataFrame(results)
df.to_excel("results/real_data_results_avg.xlsx", index=False)
print("\n实验完成！")
'''


'''
# 这是真实激活值的实验循环（探索极限版）
print(f"开始真实数据实验，共 {len(real_data_pairs)} 个场景 * {len(transform_methods)} 种变换...")
print(f"开始探索 SQH 优化极限，n={n}...")

# 第一层：遍历分组大小
for gs in group_sizes:
    print(f"\n>>> 正在测试分组大小 gs={gs} <<<")

    # 第二层：遍历真实数据配对 (Q/K/V/O)
    for w_key, x_key, scene_name in real_data_pairs:
        print(f"  - 正在寻找 {scene_name} 的 SQH 极限场景...")

        # 记录该场景下“None - SQH”差距最大的一次快照
        best_snapshot = {
            "max_diff": -1.0,
            "all_methods_mae": {},  # 存储那一次迭代中所有方法的 MAE
            "W_block": None,
            "X_block": None,
            "transformed_X": {},
            "transformed_W": {}
        }

        # 第三层：运行 n 次随机抽取实验
        for i in range(n):
            W = Wgenerator.generate(w_key)
            X = Xgenerator.generate(x_key)

            # 本次迭代临时存储各方法的误差
            current_iter_maes = {}
            current_iter_transformed_X = {}
            current_iter_transformed_W = {}

            # 第四层：遍历所有变换方法
            for method in transform_methods:
                if method == 'None':
                    t_X, t_W, T_full, T_inv_full = X, W, I, I
                else:
                    T_full = np.zeros((D, D))
                    T_inv_full = np.zeros((D, D))
                    t_X = np.zeros_like(X)
                    t_W = np.zeros_like(W)

                    for g_start in range(0, D, gs):
                        g_end = g_start + gs
                        X_g, W_g = X[g_start:g_end, :], W[g_start:g_end, :]

                        if method in ['WUSH', 'WUS', 'SQ', 'SQH']:
                            tx_g, T_g = transformer.transform(X_g, method=method, W=W_g)
                        else:
                            tx_g, T_g = transformer.transform(X_g, method=method)

                        T_g_inv = np.linalg.inv(T_g)
                        tw_g = T_g_inv.T @ W_g

                        t_X[g_start:g_end, :] = tx_g
                        t_W[g_start:g_end, :] = tw_g
                        T_full[g_start:g_end, g_start:g_end] = T_g
                        T_inv_full[g_start:g_end, g_start:g_end] = T_g_inv

                # 计算量化误差 (统一为 10^-2 单位)
                _, mae = nvfp4_quant_error(W, X, T_full, T_inv_full)
                scaled_mae = mae * 100
                current_iter_maes[method] = scaled_mae

                # 存入临时缓冲区用于可视化
                current_iter_transformed_X[method] = t_X.copy()
                current_iter_transformed_W[method] = t_W.copy()

            # --- 核心判定：寻找 SQH 提升最明显的瞬间 ---
            # 这里的 diff 代表 SQH 相比于不处理（None）降低了多少误差百分比
            improvement = (current_iter_maes['None'] - current_iter_maes['SQH']) / current_iter_maes['None']

            if improvement > best_snapshot["max_diff"]:
                best_snapshot["max_diff"] = improvement
                best_snapshot["all_methods_mae"] = current_iter_maes
                best_snapshot["W_block"] = W.copy()
                best_snapshot["X_block"] = X.copy()
                best_snapshot["transformed_X"] = current_iter_transformed_X
                best_snapshot["transformed_W"] = current_iter_transformed_W

        # --- 第五步：输出并记录该场景下的“全员成绩单” ---
        print(f"  [发现极限场景] SQH 相比 None 提升百分比: {best_snapshot['max_diff']:.4f}")
        print("  === 本次极限场景全员成绩单 (MAE 10^-2) ===")
        # 遍历打印所有方法在该次“极限时刻”的误差，使用占位符对齐排版
        for method in transform_methods:
            final_mae = best_snapshot["all_methods_mae"][method]
            print(f"    - {method:<18}: {final_mae:.4f}")

        # 遍历打印所有方法在该次“极限时刻”的误差，使用占位符对齐排版
        for method in transform_methods:
            final_mae = best_snapshot["all_methods_mae"][method]

            # 可视化保存 (基于这个极限时刻的数据)
            t_x_path = os.path.join("results/plots/activations", f"Limit_X_{scene_name}_{method}_GS{gs}.png")
            Xgenerator.visualize(best_snapshot["transformed_X"][method], title=f"Limit X: {method}", save_path=t_x_path)

            if method != 'None':
                t_w_path = os.path.join("results/plots/weights",
                                        f"Limit_W_{scene_name}_{method}_GS{gs}.png")
                Wgenerator.visualize(best_snapshot["transformed_W"][method], title=f"Limit W: {method}",
                                     save_path=t_w_path)

            # 录入结果表
            results.append({
                "场景": scene_name,
                "分组大小": gs,
                "仿射变换": method,
                "当前时刻误差 (10^-2)": round(final_mae, 4),
                "相比None的优化绝对值": round(best_snapshot["all_methods_mae"]['None'] - final_mae, 4),
                "是否为该场景最优(SQH)": "Yes" if method == "SQH" else "No"
            })

        # 单独保存一次原始权重
        w_orig_path = os.path.join("results/plots/weights", f"Limit_W_{scene_name}_GS{gs}.png")
        Wgenerator.visualize(best_snapshot["W_block"], title=f"Limit Original W: {scene_name}", save_path=w_orig_path)

        print("-" * 50)

# 导出 Excel
df = pd.DataFrame(results)
df.to_excel("results/real_data_results.xlsx", index=False)
print("\n实验完成！")
'''

# 这是峰度测试的实验循环
q_data_pairs = [pair for pair in real_data_pairs if pair[0] == 'Llama_WQ']

print(f"开始 Llama_WQ 专项峰度实验，n={n}...")

for gs in group_sizes:
    print(f"\n>>> 正在测试分组大小 gs={gs} <<<")

    for w_key, x_key, scene_name in q_data_pairs:
        # 初始化各项指标的累加器
        mae_accum = {m: 0.0 for m in transform_methods}
        kurt_W_accum = {m: 0.0 for m in transform_methods}
        kurt_X_accum = {m: 0.0 for m in transform_methods}

        for i in range(n):
            W = Wgenerator.generate(w_key)
            X = Xgenerator.generate(x_key)

            # 记录原始的峰度
            k_W_orig = kurtosis.calculate_kurtosis(W)
            k_X_orig = kurtosis.calculate_kurtosis(X)

            for method in transform_methods:
                if method == 'None':
                    t_X, t_W, T_full, T_inv_full = X, W, I, I
                else:
                    T_full, T_inv_full = np.zeros((D, D)), np.zeros((D, D))
                    t_X, t_W = np.zeros_like(X), np.zeros_like(W)

                    for g_start in range(0, D, gs):
                        g_end = g_start + gs
                        X_g, W_g = X[g_start:g_end, :], W[g_start:g_end, :]

                        # 变换
                        if method in ['WUSH', 'WUS', 'SQ', 'SQH']:
                            tx_g, T_g = transformer.transform(X_g, method=method, W=W_g)
                        else:
                            tx_g, T_g = transformer.transform(X_g, method=method)

                        T_g_inv = np.linalg.inv(T_g)
                        tw_g = T_g_inv.T @ W_g

                        t_X[g_start:g_end, :] = tx_g
                        t_W[g_start:g_end, :] = tw_g
                        T_full[g_start:g_end, g_start:g_end] = T_g
                        T_inv_full[g_start:g_end, g_start:g_end] = T_g_inv

                # 记录变换后的峰度
                k_W_trans = kurtosis.calculate_kurtosis(t_W)
                k_X_trans = kurtosis.calculate_kurtosis(t_X)

                # 累加数据
                kurt_W_accum[method] += k_W_trans
                kurt_X_accum[method] += k_X_trans

        # --- 第四步：计算平均值并输出成绩单 ---
        print(f"  === {scene_name} 实验结果汇总 (n={n}) ===")
        for method in transform_methods:
            avg_kW = kurt_W_accum[method] / n
            avg_kX = kurt_X_accum[method] / n

            # 计算峰度变化百分比
            # 基准值为 method=='None' 时的峰度
            base_kW = kurt_W_accum['None'] / n
            base_kX = kurt_X_accum['None'] / n
            kw_change = (avg_kW - base_kW) / base_kW * 100
            kx_change = (avg_kX - base_kX) / base_kX * 100

            print(f"    - {method:<12}: "
                  f"W-Kurt: {base_kW:.2f} -> {avg_kW:.2f} ({kw_change:+.1f}%), "
                  f"X-Kurt: {base_kX:.2f} -> {avg_kX:.2f} ({kx_change:+.1f}%)")

            results.append({
                "场景": scene_name,
                "分组大小": gs,
                "仿射变换": method,
                "权重基准峰度": round(base_kW, 2),
                "权重变换后峰度": round(avg_kW, 2),
                "权重峰度变化%": round(kw_change, 2),
                "激活基准峰度": round(base_kX, 2),
                "激活变换后峰度": round(avg_kX, 2),
                "激活峰度变化%": round(kx_change, 2)
            })
        print("-" * 60)



'''
# 这是用于演示的代码
# 设置参数
M, N, D = 16, 16, 16  # M: 输出维数 N: 样本数 D: 特征数
A = 5  # 离群值放大系数
n = 10  # 重复次数
Wgenerator = DataGenerator(D, M)
Xgenerator = DataGenerator(D, N)
transformer = LinearTransformer()
W = Wgenerator.generate('Llama_WQ')  # 权重矩阵
I = np.identity(D)  # 单位矩阵

for dist_key, dist_name in Xscenarios:
    total_mae_methods = {method: 0.0 for method in transform_methods}
    total_mae_methods_w = {method: 0.0 for method in transform_methods}
    custom_outlier_num = 10

    for i in range(n):
        if dist_key == 'custom_extreme':
            X = Xgenerator.generate(dist_key, scale_factor=A, num_outliers=custom_outlier_num)
        else:
            X = Xgenerator.generate(dist_key, scale_factor=A)

        # 各种转换方法
        for method in transform_methods:
            if method == 'None':
                trans_X, T = X, I
            elif method in ['WUSH', 'WUS', 'WUSH_withoutC', 'White_W']:
                trans_X, T = transformer.transform(X, method=method, W=W)
            else:
                trans_X, T = transformer.transform(X, method=method)
            E, mae = unilateral_nvfp4_quant_error(W, X, T)
            E_w, mae_w = single_matrix_quant_error(X, T)
            total_mae_methods[method] += mae
            total_mae_methods_w[method] += mae_w
            if i == 0:
                Xgenerator.visualize(trans_X, title=f"{'Llama_W_Q'} + {dist_name} + {method}")

    for method, total_mae in total_mae_methods.items():
        avg_mae_method = total_mae * 100 / N
        print(f"[{dist_name} + {method}] 转换后平均绝对误差: {avg_mae_method:.4f} (单位：10^-2)")
    for method, total_mae_w in total_mae_methods_w.items():
        avg_mae_method_w = total_mae_w * 100 / N
        print(f"[{dist_name} + {method}] 单一矩阵 X 的平均绝对误差: {avg_mae_method_w:.4f} (单位：10^-2)")
    print("-" * 50)
    '''
