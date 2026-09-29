# -*- coding: utf-8 -*-
"""图 4：训练与验证损失曲线（图例置于坐标区上方，无图内小标题）。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import params as P
from plotstyle import C_MLP, C_TMM, legend_above, panel_letter, save

m = json.loads((P.RES_DIR / "metrics_base.json").read_text(encoding="utf-8"))
tr = np.array(m["history"]["train"])
va = np.array(m["history"]["val"])
ep = np.arange(1, len(tr) + 1)
best = m["best_epoch"]

fig, axes = plt.subplots(1, 2, figsize=(5.33, 1.58))

ax = axes[0]
ax.semilogy(ep, tr, color=C_TMM, label="训练集 MSE")
ax.semilogy(ep, va, color=C_MLP, label="验证集 MSE")
ax.axvline(best, color="k", ls=":", lw=1, label=f"最佳轮次 = {best}")
ax.set_xlabel("训练轮次 epoch")
ax.set_ylabel("均方误差 MSE")
ax.set_ylim(6e-5, 6e-2)
panel_letter(ax, "a", y=1.22)
legend_above(ax, ncol=3, fs=6.4)

ax = axes[1]
tail = slice(max(0, best - 800), best + 1)
ax.semilogy(ep[tail], tr[tail], color=C_TMM, label="训练集 MSE")
ax.semilogy(ep[tail], va[tail], color=C_MLP, label="验证集 MSE")
ax.set_xlabel("训练轮次 epoch")
ax.set_ylabel("均方误差 MSE")
panel_letter(ax, "b", y=1.22)
legend_above(ax, ncol=2, fs=6.4)

fig.tight_layout()
save(fig, "fig4_training.png")
