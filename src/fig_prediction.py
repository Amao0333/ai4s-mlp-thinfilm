# -*- coding: utf-8 -*-
"""图 5：测试集上 TMM 真值与 MLP 预测的光谱对比（含散点校验）。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

import params as P
from plotstyle import C_MLP, C_ORANGE, C_TMM, panel_letter, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ev = np.load(P.RES_DIR / "base_eval.npz")
pred, true = ev["pred"], ev["true"]
ps_mae = ev["per_sample_mae"]
wl = P.WAVELENGTHS

order = np.argsort(ps_mae)
picks = [order[int(0.10 * len(order))], order[int(0.50 * len(order))], order[int(0.97 * len(order))]]
labels = ["误差较小", "误差居中", "误差较大"]

fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.0))
for li, (ax, k, lab) in enumerate(zip(axes.ravel()[:3], picks, labels)):
    ax.plot(wl, true[k], color=C_TMM, label="TMM 真值")
    ax.plot(wl, pred[k], color=C_MLP, ls="--", label="MLP 预测")
    ax.axvline(P.LAMBDA_TARGET, color=C_ORANGE, ls=":", lw=1.2)
    ax.set_xlabel("波长 λ / nm")
    ax.set_ylabel("反射率 R")
    ax.set_ylim(-0.02, 1.0)
    e = ps_mae[k]
    ax.set_title(f"{lab}  MAE = {e:.4f}")
    panel_letter(ax, "abc"[li])
    ax.legend(loc="upper right")

ax = axes.ravel()[3]
ax.scatter(true[:, I_T], pred[:, I_T], s=8, alpha=0.55, color=C_TMM, edgecolors="none")
lim = [0, 0.68]
ax.plot(lim, lim, color="k", lw=1, ls="--")
ax.set_xlim(lim)
ax.set_ylim(lim)
r = float(np.corrcoef(pred[:, I_T], true[:, I_T])[0, 1])
mae_t = float(np.mean(np.abs(pred[:, I_T] - true[:, I_T])))
ax.set_xlabel(f"TMM 真值 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_ylabel(f"MLP 预测 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_title(f"目标波长处散点  $r$ = {r:.4f}, MAE = {mae_t:.4f}")
panel_letter(ax, "d")

fig.tight_layout()
save(fig, "fig5_prediction.png")
