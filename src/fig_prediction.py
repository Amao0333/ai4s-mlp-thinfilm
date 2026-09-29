# -*- coding: utf-8 -*-
"""图 5：测试集光谱预测对比（图例置于坐标区上方，逐面板标注 MAE）。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

import params as P
from plotstyle import C_MLP, C_ORANGE, C_TMM, legend_above, panel_letter, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ev = np.load(P.RES_DIR / "base_eval.npz")
pred, true = ev["pred"], ev["true"]
ps_mae = ev["per_sample_mae"]
wl = P.WAVELENGTHS

order = np.argsort(ps_mae)
picks = [order[int(0.10 * len(order))], order[int(0.50 * len(order))], order[int(0.97 * len(order))]]

fig, axes = plt.subplots(2, 2, figsize=(5.63, 2.45))
for li, (ax, k) in enumerate(zip(axes.ravel()[:3], picks)):
    ax.plot(wl, true[k], color=C_TMM, label="TMM 真值")
    ax.plot(wl, pred[k], color=C_MLP, ls="--", label="MLP 预测")
    ax.axvline(P.LAMBDA_TARGET, color=C_ORANGE, ls=":", lw=1.2)
    ax.set_xlabel("波长 λ / nm")
    ax.set_ylabel("反射率 R")
    ax.set_ylim(-0.02, 1.0)
    ax.text(0.03, 0.95, f"MAE = {ps_mae[k]:.4f}", transform=ax.transAxes,
            va="top", fontsize=6.6)
    panel_letter(ax, "abc"[li], x=-0.28, y=(1.30 if li == 0 else 1.02))
legend_above(axes[0, 0], ncol=2, fs=6.4)

ax = axes[1, 1]
ax.scatter(true[:, I_T], pred[:, I_T], s=6, alpha=0.55, color=C_TMM, edgecolors="none")
lim = [0, 0.68]
ax.plot(lim, lim, color="k", lw=1, ls="--")
ax.set_xlim(lim)
ax.set_ylim(lim)
r = float(np.corrcoef(pred[:, I_T], true[:, I_T])[0, 1])
mae_t = float(np.mean(np.abs(pred[:, I_T] - true[:, I_T])))
ax.set_xlabel(f"TMM 真值 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_ylabel(f"MLP 预测 R({int(P.LAMBDA_TARGET)} nm)")
ax.text(0.96, 0.06, f"$r$ = {r:.4f}，MAE = {mae_t:.4f}", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=6.6)
panel_letter(ax, "d", x=-0.28)

fig.tight_layout()
save(fig, "fig5_prediction.png")
