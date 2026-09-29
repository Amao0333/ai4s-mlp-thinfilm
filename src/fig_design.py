# -*- coding: utf-8 -*-
"""图 7：MLP 辅助设计结果与 TMM 复核（图例置于坐标区上方）。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import params as P
from plotstyle import (C_GREEN, C_MLP, C_ORANGE, C_TMM, legend_above, panel_letter,
                       save)

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ds = json.loads((P.RES_DIR / "design_screening.json").read_text(encoding="utf-8"))
bound = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))
qw = json.loads((P.RES_DIR / "qw_reference.json").read_text(encoding="utf-8"))
z = np.load(P.RES_DIR / "design_screening.npz")
R_mlp, R_true = z["R_mlp"], z["R_true"]
r_mlp_t, r_true_t = z["r_mlp_target"], z["r_true_target"]
order_mlp = z["order_mlp"]
top5 = ds["final_top5"]
k1 = top5[0]["sample_index"]

fig, axes = plt.subplots(1, 2, figsize=(5.33, 1.72))

ax = axes[0]
ax.plot(P.WAVELENGTHS, R_true[k1], color=C_TMM, label="TMM 真值")
ax.plot(P.WAVELENGTHS, R_mlp[k1], color=C_MLP, ls="--", label="MLP 预测")
ax.plot(P.WAVELENGTHS, qw["spectrum_R"], color="#999999", lw=0.9, ls="-.", label="四分之一波长参考")
ax.axhline(bound["R_bound"], color=C_ORANGE, ls=":", lw=1.1, label="R 物理上限")
ax.axvline(P.LAMBDA_TARGET, color="#555555", ls=":", lw=0.9)
ax.plot([P.LAMBDA_TARGET], [R_true[k1, I_T]], "o", color=C_TMM, ms=3.5)
ax.text(0.96, 0.06, f"$R_{{TMM}}$ = {R_true[k1, I_T]:.4f}\n$R_{{MLP}}$ = {R_mlp[k1, I_T]:.4f}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=6.4)
ax.set_xlabel("波长 λ / nm")
ax.set_ylabel("反射率 R")
ax.set_ylim(0, 0.78)
panel_letter(ax, "a", y=1.42)
legend_above(ax, ncol=2, fs=6.2)

ax = axes[1]
ax.scatter(r_true_t, r_mlp_t, s=2, alpha=0.30, color="#8fa8bf", edgecolors="none",
           label="10000 组候选")
ax.scatter(r_true_t[order_mlp[:10]], r_mlp_t[order_mlp[:10]], s=16, color=C_MLP,
           marker="^", label="MLP Top10")
ax.scatter([ds["best_of_pool"]["R_tmm_target"]], [r_mlp_t[order_mlp[0]]], s=28,
           facecolors="none", edgecolors=C_GREEN, linewidths=1.1, label="全批最优")
ax.plot([0, 0.7], [0, 0.7], color="k", ls="--", lw=0.9)
ax.text(0.04, 0.96, f"Spearman ρ = {ds['ranking']['spearman_rho']:.4f}", transform=ax.transAxes,
        va="top", fontsize=6.4)
ax.set_xlabel(f"TMM 真值 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_ylabel(f"MLP 预测 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_xlim(0, 0.70)
ax.set_ylim(0, 0.70)
panel_letter(ax, "b", y=1.32)
legend_above(ax, ncol=2, fs=6.2)

fig.tight_layout()
save(fig, "fig7_design.png")
