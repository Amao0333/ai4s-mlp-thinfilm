# -*- coding: utf-8 -*-
"""图 8：代表性失败案例与误差归因。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr

import params as P
from plotstyle import C_MLP, C_ORANGE, C_TMM, panel_letter, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ev = np.load(P.RES_DIR / "base_eval.npz")
pred, true = ev["pred"], ev["true"]
ps_mse, ps_max = ev["per_sample_mse"], ev["per_sample_maxabs"]
att = json.loads((P.RES_DIR / "attribution.json").read_text(encoding="utf-8"))
w = att["worst_cases"][0]
k = w["test_pos"]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))

ax = axes[0]
ax.plot(P.WAVELENGTHS, true[k], color=C_TMM, label="TMM 真值")
ax.plot(P.WAVELENGTHS, pred[k], color=C_MLP, ls="--", label="MLP 预测")
ax.fill_between(P.WAVELENGTHS, true[k], pred[k], color=C_ORANGE, alpha=0.20,
                label="预测偏差")
ax.axvline(P.LAMBDA_TARGET, color="#555555", ls=":", lw=1.0)
ax.set_xlabel("波长 λ / nm")
ax.set_ylabel("反射率 R")
ax.set_ylim(-0.02, 0.85)
d_txt = ", ".join(f"{x:.1f}" for x in w["d_nm"])
ax.set_title(f"最大误差样本  MAE = {w['per_sample_mae']:.4f}", fontsize=9.5)
panel_letter(ax, "a")
ax.text(0.03, 0.92, f"膜厚 = ({d_txt}) nm", transform=ax.transAxes, va="top", fontsize=7.0,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#cccccc", alpha=0.92))
ax.legend(loc="upper left", fontsize=7.0,
          frameon=True, framealpha=0.92, edgecolor="#cccccc")

ax = axes[1]
cv = np.load(P.RES_DIR / "coverage.npz")
d10, mse_cv = cv["d10"], cv["ps_mse"]
ax.scatter(d10, mse_cv, s=8, alpha=0.45, color="#8fa8bf", edgecolors="none",
           label="500 个测试样本")
ax.scatter([d10[k]], [mse_cv[k]], s=40, facecolors="none", edgecolors=C_MLP,
           linewidths=1.3, label="最大误差样本")
r = pearsonr(d10, mse_cv)
co = json.loads((P.RES_DIR / "coverage.json").read_text(encoding="utf-8"))
q = np.quantile(d10, [0, 0.25, 0.5, 0.75, 1.0])
centers, med = [], []
for i in range(4):
    m = (d10 >= q[i]) & (d10 <= q[i + 1] if i == 3 else d10 < q[i + 1])
    centers.append(float(np.median(d10[m])))
    med.append(float(np.mean(mse_cv[m])))
ax.plot(centers, med, "o-", color=C_ORANGE, lw=1.4, ms=4, label="四分位分箱均值")
z = np.polyfit(d10, mse_cv, 1)
xs = np.linspace(d10.min(), d10.max(), 20)
ax.plot(xs, np.polyval(z, xs), color=C_TMM, lw=1.1, ls="--", label="线性拟合")
ax.set_xlabel("第 10 近邻距离（归一化膜厚空间）")
ax.set_ylabel("逐样本 MSE")
ratio = co["bins_by_d5"][3]["mse_mean"] / co["bins_by_d5"][0]["mse_mean"] - 1
ax.text(0.03, 0.95, f"Pearson r = {r.statistic:.3f}，$r^2$ = {r.statistic ** 2:.3f}",
        transform=ax.transAxes, va="top", fontsize=7.4)
ax.text(0.03, 0.86, f"稀疏组 MSE 比密集组高 {ratio:.0%}",
        transform=ax.transAxes, va="top", fontsize=7.4)
ax.legend(loc="upper right", fontsize=6.8, frameon=True,
          framealpha=0.92, edgecolor="#cccccc")
ax.set_title("误差随局部采样稀疏度上升", fontsize=9.5)
panel_letter(ax, "b")
fig.tight_layout()
save(fig, "fig8_failure.png")
