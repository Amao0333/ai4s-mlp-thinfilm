# -*- coding: utf-8 -*-
"""图 2：物理模型与 TMM 数据生成（三面板）。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import params as P
import tmm
from plotstyle import C_GREEN, C_LABEL, C_MLP, C_ORANGE, C_TMM, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
D = np.load(P.DATA_NPZ)
Dall, Rall = D["D"], D["R"]
stats = json.loads((P.RES_DIR / "dataset_stats.json").read_text(encoding="utf-8"))
qw = json.loads((P.RES_DIR / "qw_reference.json").read_text(encoding="utf-8"))


def letter(ax, s, x=-0.20, y=1.02):
    ax.text(x, y, s, transform=ax.transAxes, ha="left", va="bottom", fontsize=8.5,
            color="white", fontweight="bold", zorder=8,
            bbox=dict(boxstyle="square,pad=0.26", facecolor=C_LABEL, edgecolor="none"))


fig = plt.figure(figsize=(5.33, 2.15))
gs = fig.add_gridspec(1, 3, width_ratios=[0.86, 1.20, 1.00], wspace=0.46)

# ---------------- (a) 膜系结构 ----------------
ax = fig.add_subplot(gs[0, 0])
names = ["Air", "H", "L", "H", "L", "Glass"]
idx = [P.N_INCIDENT, P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW, P.N_SUBSTRATE]
fills = ["#f2f2f2", "#fbe5d6", "#dae3f3", "#fbe5d6", "#dae3f3", "#e2efda"]
edges = ["#bfbfbf", "#f4b183", "#8eaadb", "#f4b183", "#8eaadb", "#a9d08e"]
y = 0.0
for i, (nm, n, fc, ec) in enumerate(zip(names, idx, fills, edges)):
    h = 0.40 if i in (0, len(names) - 1) else 0.80
    ax.add_patch(FancyBboxPatch((0.0, y), 1.0, h,
                                boxstyle="round,pad=0.002,rounding_size=0.02",
                                facecolor=fc, edgecolor=ec, linewidth=1.0))
    ax.text(0.5, y + h / 2, f"{nm}   n={n:.2f}", ha="center", va="center",
            fontsize=6.8)
    if 0 < i < len(names) - 1:
        ax.text(1.04, y + h / 2, f"$d_{i}$", ha="left", va="center", fontsize=7.6)
    y += h

ax.add_patch(FancyArrowPatch((0.10, -0.60), (0.38, -0.04), arrowstyle="-|>",
                             mutation_scale=9, color=C_TMM, lw=1.2))
ax.add_patch(FancyArrowPatch((0.62, -0.04), (0.90, -0.60), arrowstyle="-|>",
                             mutation_scale=9, color=C_MLP, lw=1.2))
ax.text(0.05, -0.62, "入射", ha="center", va="top", fontsize=7.2, color=C_TMM)
ax.text(0.95, -0.70, "反射", ha="center", va="top", fontsize=7.0, color=C_MLP)
ax.text(0.5, -1.02, "每层 40–180 nm，正入射", ha="center", va="top", fontsize=6.8,
        color="#555555")
ax.set_xlim(-0.18, 1.36)
ax.set_ylim(-1.22, y + 0.04)
ax.axis("off")
letter(ax, "a")
ax.set_title("膜系结构", fontsize=9.0, pad=12)

# ---------------- (b) 代表性光谱 ----------------
ax = fig.add_subplot(gs[0, 1])
d_qw = np.array(qw["thickness_nm"])
cases = [(d_qw, "四分之一波长膜系", C_ORANGE),
         (Dall[0], "随机膜系 #1", C_TMM),
         (Dall[1234], "随机膜系 #2", C_GREEN)]
for ds, lab, c in cases:
    ax.plot(P.WAVELENGTHS, tmm.reflectance_char_matrix(ds)[0], color=c, label=lab)
ax.axvline(P.LAMBDA_TARGET, color="#888888", ls=":", lw=1.1)

ax.set_xlabel("波长 λ / nm", fontsize=8.5)
ax.set_ylabel("反射率 R", fontsize=8.5)
ax.set_ylim(-0.02, 1.05)
ax.legend(loc="upper right", fontsize=6.8, frameon=True, framealpha=0.92,
          edgecolor="#cccccc")
letter(ax, "b")
ax.set_title("TMM 反射光谱", fontsize=9.0, pad=10)

# ---------------- (c) 目标波长处 R 分布 ----------------
ax = fig.add_subplot(gs[0, 2])
edges = np.array(stats["hist_R_at_target"]["edges"])
counts = np.array(stats["hist_R_at_target"]["counts"])
ax.bar(edges[:-1], counts, width=np.diff(edges), align="edge",
       color="#9fb6cd", edgecolor="#5b7c99", linewidth=0.4)
ax.axvline(qw["R_analytic"], color=C_ORANGE, ls="--", lw=1.3,
           label=f"物理上限 {qw['R_analytic']:.4f}")
ax.set_xlabel(f"R({int(P.LAMBDA_TARGET)} nm)", fontsize=8.5)
ax.set_ylabel("样本数", fontsize=8.5)
ax.set_xlim(0, 0.70)
ax.legend(loc="upper left", fontsize=6.4, handlelength=1.2, frameon=True,
          framealpha=0.92, edgecolor="#cccccc")
letter(ax, "c")
ax.set_title("目标波长处 R 的分布", fontsize=9.0, pad=10)

save(fig, "fig2_model_data.png")
