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
ax.text(0.03, 0.06, f"膜厚 = ({d_txt}) nm", transform=ax.transAxes, fontsize=7.4)
ax.legend(loc="upper left", fontsize=7.4)

ax = axes[1]
dR = np.abs(np.diff(true, axis=1)).mean(axis=1)
ax.scatter(dR, ps_mse, s=8, alpha=0.5, color="#8fa8bf", edgecolors="none")
ax.scatter([dR[k]], [ps_mse[k]], s=40, facecolors="none", edgecolors=C_MLP,
           linewidths=1.3, label="最差样本")
r = pearsonr(dR, ps_mse)
z = np.polyfit(dR, ps_mse, 1)
xs = np.linspace(dR.min(), dR.max(), 20)
ax.plot(xs, np.polyval(z, xs), color=C_TMM, lw=1.2, ls="--", label="线性拟合")
ax.set_xlabel("光谱平均斜率 |ΔR| / 10 nm")
ax.set_ylabel("逐样本 MSE")
ax.text(0.03, 0.95, f"Pearson r = {r.statistic:.3f}\n(p = {r.pvalue:.1e})",
        transform=ax.transAxes, va="top", fontsize=7.6)
ax.legend(loc="lower right", fontsize=7.2)
ax.set_title("误差随光谱陡峭度上升", fontsize=9.5)
panel_letter(ax, "b")

fig.tight_layout()
save(fig, "fig8_failure.png")
