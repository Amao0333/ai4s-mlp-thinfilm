# -*- coding: utf-8 -*-
"""图 6：训练数据量对测试误差的影响（图例置于坐标区上方）。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import params as P
from plotstyle import C_GREEN, C_MLP, C_TMM, legend_above, panel_letter, save

se = json.loads((P.RES_DIR / "size_experiment.json").read_text(encoding="utf-8"))
lv = se["levels"]
fit = se["power_law_fit"]
N = np.array([l["n_train"] for l in lv], dtype=float)
mse = np.array([l["test_mse_mean"] for l in lv])
mse_sd = np.array([l["test_mse_std"] for l in lv])
mae = np.array([l["test_mae_mean"] for l in lv])
mae_sd = np.array([l["test_mae_std"] for l in lv])

fig, axes = plt.subplots(1, 2, figsize=(5.33, 1.62))

ax = axes[0]
ax.errorbar(N, mse, yerr=mse_sd, marker="o", ms=3.5, color=C_TMM, capsize=2.5,
            label="测试 MSE（3 种子）")
xs = np.logspace(np.log10(N.min()), np.log10(N.max()), 50)
ax.plot(xs, np.exp(fit["a"]) * xs ** (-fit["alpha"]), color=C_MLP, ls="--", lw=1.1,
        label=f"幂律拟合 ∝$N^{{-{fit['alpha']:.3f}}}$")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("训练样本数 N")
ax.set_ylabel("测试集 MSE")
ax.set_xticks(N)
ax.set_xticklabels([f"{int(v)}" for v in N])
ax.minorticks_off()
ax.set_ylim(4e-5, 3e-3)
ax.text(0.04, 0.06, f"$R^2$ = {fit['r2']:.4f}", transform=ax.transAxes, fontsize=6.8)
panel_letter(ax, "a", y=1.30)
legend_above(ax, ncol=2, fs=6.2)

ax = axes[1]
ax.errorbar(N, mae, yerr=mae_sd, marker="s", ms=3.5, color=C_GREEN, capsize=2.5)
for x, y in zip(N, mae):
    ax.annotate(f"{y:.4f}", (x, y), textcoords="offset points", xytext=(0, 6),
                ha="center", fontsize=6.4)
ax.set_xlabel("训练样本数 N")
ax.set_ylabel("测试集平均绝对误差 MAE")
ax.set_ylim(0.004, max(mae) * 1.16)
ax.set_xticks(N)
ax.set_xticklabels([f"{int(v)}" for v in N])
panel_letter(ax, "b")

fig.tight_layout()
save(fig, "fig6_datasize.png")
