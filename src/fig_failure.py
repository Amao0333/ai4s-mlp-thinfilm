# -*- coding: utf-8 -*-
"""图 8：代表性失败案例与误差归因（图例置于坐标区上方）。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr

import params as P
from plotstyle import C_MLP, C_ORANGE, C_TMM, legend_above, panel_letter, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ev = np.load(P.RES_DIR / "base_eval.npz")
pred, true = ev["pred"], ev["true"]
ps_mse = ev["per_sample_mse"]
att = json.loads((P.RES_DIR / "attribution.json").read_text(encoding="utf-8"))
k = att["worst_cases"][0]["test_pos"]

fig, axes = plt.subplots(1, 2, figsize=(5.33, 1.72))

ax = axes[0]
ax.plot(P.WAVELENGTHS, true[k], color=C_TMM, label="TMM 真值")
ax.plot(P.WAVELENGTHS, pred[k], color=C_MLP, ls="--", label="MLP 预测")
ax.fill_between(P.WAVELENGTHS, true[k], pred[k], color=C_ORANGE, alpha=0.20,
                label="预测偏差")
ax.axvline(P.LAMBDA_TARGET, color="#555555", ls=":", lw=0.9)
ax.set_xlabel("波长 λ / nm")
ax.set_ylabel("反射率 R")
ax.set_ylim(-0.02, 0.85)
panel_letter(ax, "a", y=1.32)
legend_above(ax, ncol=3, fs=6.2)

ax = axes[1]
cv = np.load(P.RES_DIR / "coverage.npz")
d10, mse_cv = cv["d10"], cv["ps_mse"]
ax.scatter(d10, mse_cv, s=5, alpha=0.45, color="#8fa8bf", edgecolors="none",
           label="500 个测试样本")
ax.scatter([d10[k]], [mse_cv[k]], s=26, facecolors="none", edgecolors=C_MLP,
           linewidths=1.1, label="最大误差样本")
q = np.quantile(d10, [0, 0.25, 0.5, 0.75, 1.0])
centers, med = [], []
for i in range(4):
    m = (d10 >= q[i]) & (d10 <= q[i + 1] if i == 3 else d10 < q[i + 1])
    centers.append(float(np.median(d10[m])))
    med.append(float(np.mean(mse_cv[m])))
ax.plot(centers, med, "o-", color=C_ORANGE, lw=1.2, ms=3, label="四分位均值")
z = np.polyfit(d10, mse_cv, 1)
xs = np.linspace(d10.min(), d10.max(), 20)
ax.plot(xs, np.polyval(z, xs), color=C_TMM, lw=1.0, ls="--", label="线性拟合")
r = pearsonr(d10, mse_cv)
ax.text(0.03, 0.96, f"$r$ = {r.statistic:.3f}，$r^2$ = {r.statistic ** 2:.3f}",
        transform=ax.transAxes, va="top", fontsize=6.4)
ax.set_xlabel("第 10 近邻距离（归一化膜厚空间）")
ax.set_ylabel("逐样本 MSE")
panel_letter(ax, "b", y=1.32)
legend_above(ax, ncol=2, fs=6.2)

fig.tight_layout()
save(fig, "fig8_failure.png")
