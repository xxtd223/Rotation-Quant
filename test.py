import torch

# 加载文件
xq = torch.load('activations_output/Llama_XQ.pt', map_location='cpu')
xk = torch.load('activations_output/Llama_XK.pt', map_location='cpu')
xv = torch.load('activations_output/Llama_XV.pt', map_location='cpu')
xo = torch.load('activations_output/Llama_XO.pt', map_location='cpu')

# 验证 Q, K, V 的输入是否一致
print(f"XQ shape: {xq.shape}, XK shape: {xk.shape}, XV shape: {xv.shape}")
print(f"XQ vs XK 是否完全相等: {torch.equal(xq, xk)}")
print(f"XQ vs XV 是否完全相等: {torch.equal(xq, xv)}")

# 验证 XQ 与 XO 的差异
mse_dist = torch.nn.functional.mse_loss(xq.float(), xo.float())
print(f"XQ vs XO 的均方误差 (MSE): {mse_dist.item():.6f}")

# 查看具体数值分布（例如前5个元素）
print(f"\nXQ 前5个元素: \n{xq.flatten()[:5]}")
print(f"\nXK 前5个元素: \n{xk.flatten()[:5]}")
print(f"\nXV 前5个元素: \n{xv.flatten()[:5]}")
print(f"\nXO 前5个元素: \n{xo.flatten()[:5]}")