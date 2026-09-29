# -*- coding: utf-8 -*-
"""图 3：MLP 代理模型结构。

制图说明：不绘制全连接细线（缩印后必然糊成一团），改用块状图 + 层间箭头，
符合现代论文的架构图惯例。多行文字用 NL 拼接，避免转义问题。
"""
from __future__ import annotations

import matplotlib.pyplot as plt

import params as P
from plotstyle import arrow, panel_frame, panel_label, rbox, save

NL = chr(10)

fig, ax = plt.subplots(figsize=(5.33, 2.20))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ---------------- (a) 网络结构 ----------------
panel_frame(ax, 0.012, 0.030, 0.700, 0.985)
panel_label(ax, 0.028, 0.972, "a")
ax.text(0.350, 0.900, "网络结构", ha="center", va="center", fontsize=8.5)

BLOCKS = [
    (0.020, "输入" + NL + "4 层膜厚", "input"),
    (0.159, "全连接 128" + NL + "ReLU", "model"),
    (0.298, "全连接 128" + NL + "ReLU", "model"),
    (0.437, "全连接 64" + NL + "ReLU", "model"),
    (0.576, "输出 41" + NL + "R(λ)", "output"),
]
W, Y, H = 0.115, 0.520, 0.250
for x, text, kind in BLOCKS:
    rbox(ax, x, Y, W, H, text, kind, fs=6.2, ls=1.5)
for x, _, _ in BLOCKS[:-1]:
    arrow(ax, (x + W + 0.003, Y + H / 2), (x + W + 0.019, Y + H / 2),
          color="#404040", lw=1.2, ms=7)

ax.text(0.350, 0.400, "输入：归一化到 [0,1] 的四层膜厚", ha="center", va="center", fontsize=6.4)
ax.text(0.350, 0.310, "输出：41 点反射率光谱", ha="center", va="center", fontsize=6.4)
ax.text(0.350, 0.180, "参数量约 2.7×10$^4$", ha="center", va="center", fontsize=6.4)

# ---------------- (b) 训练设置 ----------------
panel_frame(ax, 0.720, 0.030, 0.988, 0.985)
panel_label(ax, 0.736, 0.972, "b")
ax.text(0.854, 0.900, "训练设置", ha="center", va="center", fontsize=8.5)

SETTINGS = [
    ("损失 MSE", "model"),
    ("Adam  3×10$^{-3}$", "input"),
    ("批大小 256", "input"),
    ("最多 4000 轮", "output"),
    ("早停 400 轮", "output"),
]
for i, (text, kind) in enumerate(SETTINGS):
    yy = 0.760 - 0.140 * i
    rbox(ax, 0.736, yy - 0.070, 0.238, 0.092, text, kind, fs=6.4)

save(fig, "fig3_arch.png")
