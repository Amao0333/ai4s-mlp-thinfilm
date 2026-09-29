# -*- coding: utf-8 -*-
"""图 6：训练数据量对测试误差的影响。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import params as P
from plotstyle import C_GREEN, C_MLP, C_TMM, panel_letter, save

se = json.loads((P.RES_DIR / "size_experiment.json").read_text(encoding="utf-8"))
levels = se["levels"]
fit = se["power_law_fit"]
N = np.array([lv["n_train"] for lv in levels], dtype=float)
mse = np.array([lv["test_mse_mean"] for lv in levels])
mse_sd = np.array([lv["test_mse_std"] for lv in levels])
mae = np.array([lv["test_mae_mean"] for lv in levels])
mae_sd = np.array([lv["test_mae_std"] for lv in levels])

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))

ax = axes[0]
ax.errorbar(N, mse, yerr=mse_sd, marker="o", ms=4, color=C_TMM, capsize=3,
            label="测试集 MSE（3 个初始化种子）")
xs = np.logspace(np.log10(N.min()), np.log10(N.max()), 50)
ax.plot(xs, np.exp(fit["a"]) * xs ** (-fit["alpha"]), color=C_MLP, ls="--", lw=1.2,
        label=f"幂律拟合 $\propto N^{{-{fit['alpha']:.3f}}}$")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("训练样本数 N")
ax.set_ylabel("测试集 MSE")
ax.text(0.04, 0.06, f"$R^2$ = {fit['r2']:.4f}", transform=ax.transAxes, fontsize=7.4)
ax.set_xticks(N)
ax.set_xticklabels([f"{int(v)}" for v in N])
ax.minorticks_off()
ax.legend(loc="upper right", fontsize=6.8)
ax.set_title("误差随数据量的幂律下降", fontsize=9.5)
panel_letter(ax, "a")

ax = axes[1]
ax.errorbar(N, mae, yerr=mae_sd, marker="s", ms=4, color=C_GREEN, capsize=3,
            label="测试集 MAE")
for x, y in zip(N, mae):
    ax.annotate(f"{y:.4f}", (x, y), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=7.2)
ax.set_xlabel("训练样本数 N")
ax.set_ylabel("测试集平均绝对误差 MAE")
ax.set_ylim(0.005, max(mae) * 1.30)
ax.set_xticks(N)
ax.set_xticklabels([f"{int(v)}" for v in N])
ax.legend(loc="upper right", fontsize=7.0)
ax.set_title("边际收益递减", fontsize=9.5)
panel_letter(ax, "b")

fig.tight_layout()
save(fig, "fig6_datasize.png")
