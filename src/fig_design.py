# -*- coding: utf-8 -*-
"""图 7：MLP 辅助设计结果与 TMM 复核。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

import params as P
from plotstyle import C_GREEN, C_MLP, C_ORANGE, C_TMM, panel_letter, save

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ds = json.loads((P.RES_DIR / "design_screening.json").read_text(encoding="utf-8"))
bound = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))
qw = json.loads((P.RES_DIR / "qw_reference.json").read_text(encoding="utf-8"))
z = np.load(P.RES_DIR / "design_screening.npz")
D_des, R_mlp, R_true = z["D_des"], z["R_mlp"], z["R_true"]
r_mlp_t, r_true_t = z["r_mlp_target"], z["r_true_target"]
order_mlp = z["order_mlp"]

top5 = ds["final_top5"]
k1 = top5[0]["sample_index"]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))

ax = axes[0]
ax.plot(P.WAVELENGTHS, R_true[k1], color=C_TMM, label="TMM 真值（最终设计）")
ax.plot(P.WAVELENGTHS, R_mlp[k1], color=C_MLP, ls="--", label="MLP 预测")
ax.plot(P.WAVELENGTHS, qw["spectrum_R"], color="#999999", lw=1.0, ls="-.",
        label="四分之一波长参考")
ax.axhline(bound["R_bound"], color=C_ORANGE, ls=":", lw=1.2, label="R 物理上限")
ax.axvline(P.LAMBDA_TARGET, color="#555555", ls=":", lw=1.0)
ax.plot([P.LAMBDA_TARGET], [R_true[k1, I_T]], "o", color=C_TMM, ms=4)
ax.annotate(f"$R_{{TMM}}$ = {R_true[k1, I_T]:.4f}\n$R_{{MLP}}$ = {R_mlp[k1, I_T]:.4f}",
            xy=(P.LAMBDA_TARGET, R_true[k1, I_T]), xytext=(P.LAMBDA_TARGET + 75, 0.44),
            fontsize=7.6, arrowprops=dict(arrowstyle="-", lw=0.8, color="#666666"))
ax.set_xlabel("波长 λ / nm")
ax.set_ylabel("反射率 R")
ax.set_ylim(0, 0.72)
ax.legend(loc="lower left", fontsize=6.8, frameon=True,
          framealpha=0.92, edgecolor="#cccccc")
ax.set_title("最终设计的预测与复核光谱", fontsize=9.5)
panel_letter(ax, "a")

ax = axes[1]
ax.scatter(r_true_t, r_mlp_t, s=3, alpha=0.35, color="#8fa8bf", edgecolors="none",
           label="10000 组候选")
ax.scatter(r_true_t[order_mlp[:10]], r_mlp_t[order_mlp[:10]], s=22, color=C_MLP,
           marker="^", label="MLP 排序 Top10")
ax.scatter([ds["best_of_pool"]["R_tmm_target"]], [r_mlp_t[order_mlp[0]]], s=40,
           facecolors="none", edgecolors=C_GREEN, linewidths=1.3, label="全批 TMM 最优")
ax.plot([0, 0.7], [0, 0.7], color="k", ls="--", lw=1.0)
rho = ds["ranking"]["spearman_rho"]
ax.set_xlabel(f"TMM 真值 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_ylabel(f"MLP 预测 R({int(P.LAMBDA_TARGET)} nm)")
ax.set_xlim(0, 0.70)
ax.set_ylim(0, 0.70)
ax.text(0.03, 0.95, f"Spearman ρ = {rho:.4f}\nTop10 召回率 = {ds['ranking']['top10_recall_vs_tmm_top10']:.0%}",
        transform=ax.transAxes, va="top", fontsize=7.6)
ax.legend(loc="lower right", fontsize=7.0)
ax.set_title("候选池排名一致性", fontsize=9.5)
panel_letter(ax, "b")

fig.tight_layout()
save(fig, "fig7_design.png")
