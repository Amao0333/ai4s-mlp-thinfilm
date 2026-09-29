# -*- coding: utf-8 -*-
"""图 3：MLP 代理模型结构（两面板）。"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

import params as P
from plotstyle import PALETTE, panel_frame, panel_label, rbox, save

fig, ax = plt.subplots(figsize=(5.33, 2.44))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ---------------- (a) 网络结构 ----------------
panel_frame(ax, 0.012, 0.030, 0.700, 0.985)
panel_label(ax, 0.028, 0.972, "a")
ax.text(0.36, 0.945, "网络结构", ha="center", va="center", fontsize=8.2)

ax.add_patch(FancyBboxPatch((0.030, 0.205), 0.655, 0.700,
                            boxstyle="round,pad=0.006,rounding_size=0.03",
                            linewidth=1.1, facecolor="#fdf2e3", edgecolor="#e8b87a",
                            zorder=0))
ax.text(0.640, 0.855, "MLP 代理模型", ha="right", va="center", fontsize=7.6, color="#9c6b23")

cols = [(0.095, 4, "输入层", "input"), (0.265, 10, "128", "model"),
        (0.420, 10, "128", "model"), (0.565, 8, "64", "model"),
        (0.660, 10, "41", "output")]
ys = {}
y0, y1 = 0.330, 0.700

for x, n, lab, kind in cols:
    pos = [y0 + (y1 - y0) * i / (n - 1) for i in range(n)]
    ys[x] = pos
    st = PALETTE[kind]
    for y in pos:
        ax.add_patch(Circle((x, y), 0.0145, facecolor=st["fc"], edgecolor=st["ec"],
                            linewidth=1.0, zorder=4))
    ax.text(x, 0.730, lab, ha="center", va="bottom", fontsize=8.0, zorder=5)

for x1, x2 in [(0.095, 0.265), (0.265, 0.420), (0.420, 0.565), (0.565, 0.660)]:
    for ya in ys[x1]:
        for yb in ys[x2]:
            ax.plot([x1 + 0.0145, x2 - 0.0145], [ya, yb], color="#b8c9da", lw=0.10,
                    alpha=0.55, zorder=1)

for x in [0.265, 0.420, 0.565]:
    ax.text(x + 0.040, 0.515, "ReLU", ha="left", va="center", fontsize=7.0,
            color="#c00000", rotation=90, zorder=5)

for y, lab in zip(ys[0.095], ["$d_1$ (H)", "$d_2$ (L)", "$d_3$ (H)", "$d_4$ (L)"]):
    ax.text(0.085, y, lab, ha="right", va="center", fontsize=7.6)

ax.text(0.357, 0.150, "输入 4 层膜厚，输出 41 点光谱", ha="center", va="center", fontsize=7.0)
ax.text(0.357, 0.080, "参数量约 2.7×10$^4$", ha="center", va="center", fontsize=7.0)

# ---------------- (b) 训练设置 ----------------
panel_frame(ax, 0.735, 0.030, 0.988, 0.985)
panel_label(ax, 0.751, 0.972, "b")
ax.text(0.862, 0.945, "训练设置", ha="center", va="center", fontsize=8.2)

settings = [
    ("损失：MSE", "model"),
    ("Adam  3×10$^{-3}$", "input"),
    ("批大小 256", "input"),
    ("最多 4000 轮", "output"),
    ("早停 400 轮", "output"),
]
for i, (val, kind) in enumerate(settings):
    yy = 0.860 - 0.150 * i
    rbox(ax, 0.752, yy - 0.075, 0.230, 0.085, val, kind, fs=6.8)

save(fig, "fig3_arch.png")
