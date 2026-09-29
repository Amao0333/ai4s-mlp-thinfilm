# -*- coding: utf-8 -*-
"""图 3：MLP 代理模型结构。

输入层标签的位置由文字实际渲染宽度反推，既不留白也不越界。
"""
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
ax.text(0.360, 0.945, "网络结构", ha="center", va="center", fontsize=8.2)

ax.add_patch(FancyBboxPatch((0.030, 0.205), 0.655, 0.700,
                            boxstyle="round,pad=0.006,rounding_size=0.03",
                            linewidth=1.1, facecolor="#fdf2e3", edgecolor="#e8b87a",
                            zorder=0))
ax.text(0.640, 0.855, "MLP 代理模型", ha="right", va="center", fontsize=7.6, color="#9c6b23")

# 先量出输入层标签的实际宽度，再据此确定输入列位置
LABELS = ["$d_1$ (H)", "$d_2$ (L)", "$d_3$ (H)", "$d_4$ (L)"]
probe = ax.text(0.5, 0.5, "$d_3$ (H)", ha="right", va="center", fontsize=7.6)
fig.canvas.draw()
rend = fig.canvas.get_renderer()
inv = ax.transAxes.inverted()
bb = probe.get_window_extent(renderer=rend)
label_w = inv.transform((bb.x1, 0))[0] - inv.transform((bb.x0, 0))[0]
probe.remove()

LEFT_MARGIN = 0.042                 # 标签左端距画布左边的留白
label_right = LEFT_MARGIN + label_w  # 标签右端（即输入节点左侧）
input_x = label_right + 0.016        # 输入节点列位置

# 各列相对输入列的偏移量
OFFSETS = [(0.000, 4, "输入层", "input"), (0.140, 10, "128", "model"),
           (0.260, 10, "128", "model"), (0.375, 8, "64", "model"),
           (0.463, 10, "41", "output")]
cols = [(input_x + dx, n, lab, kind) for dx, n, lab, kind in OFFSETS]

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

xs = [c[0] for c in cols]
for x1, x2 in zip(xs[:-1], xs[1:]):
    for ya in ys[x1]:
        for yb in ys[x2]:
            ax.plot([x1 + 0.0145, x2 - 0.0145], [ya, yb], color="black", lw=0.22,
                    alpha=0.35, zorder=1)

for y, lab in zip(ys[xs[0]], LABELS):
    ax.text(label_right, y, lab, ha="right", va="center", fontsize=7.6)

ax.text(0.365, 0.150, "输入 4 层膜厚，输出 41 点光谱，隐藏层激活 ReLU",
        ha="center", va="center", fontsize=7.0)
ax.text(0.365, 0.080, "参数量约 2.7×10$^4$，全连接", ha="center", va="center", fontsize=7.0)

# ---------------- (b) 训练设置 ----------------
panel_frame(ax, 0.720, 0.030, 0.988, 0.985)
panel_label(ax, 0.736, 0.972, "b")
ax.text(0.854, 0.945, "训练设置", ha="center", va="center", fontsize=8.2)

SETTINGS = [
    ("损失：MSE", "model"),
    ("Adam  3×10$^{-3}$", "input"),
    ("批大小 256", "input"),
    ("最多 4000 轮", "output"),
    ("早停 400 轮", "output"),
]
for i, (text, kind) in enumerate(SETTINGS):
    yy = 0.800 - 0.145 * i
    rbox(ax, 0.736, yy - 0.045, 0.238, 0.090, text, kind, fs=6.6)

save(fig, "fig3_arch.png")
