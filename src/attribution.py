# -*- coding: utf-8 -*-
"""第 11 步：逐样本误差归因 —— 误差与哪些物理特征相关，失败案例长什么样。

输出 results/attribution.json
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import pearsonr, spearmanr

import params as P

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))

d = np.load(P.DATA_NPZ)
D_all = d["D"]
ev = np.load(P.RES_DIR / "base_eval.npz")
pred, true, idx_test = ev["pred"], ev["true"], ev["idx_test"]
ps_mse, ps_mae, ps_max = ev["per_sample_mse"], ev["per_sample_mae"], ev["per_sample_maxabs"]

D = D_all[idx_test]
n_idx = np.array([P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW])
opt_thick = (D * n_idx).sum(axis=1)

dR = np.diff(true, axis=1)
fringe_mean = np.abs(dR).mean(axis=1)
sign = np.sign(dR)
n_extrema = np.sum((sign[:, 1:] * sign[:, :-1]) < 0, axis=1)
R_target = true[:, I_T]
slope_target = (true[:, I_T + 1] - true[:, I_T - 1]) / (2 * P.WL_STEP)
sharpness = np.abs(slope_target)
R_std = true.std(axis=1)

features = {
    "total_optical_thickness_nm": opt_thick,
    "mean_abs_dR_per_10nm": fringe_mean,
    "n_local_extrema": n_extrema.astype(float),
    "R_at_target": R_target,
    "abs_slope_at_target": sharpness,
    "R_std_over_spectrum": R_std,
}

corr = {}
for k, v in features.items():
    pr = pearsonr(v, ps_mse)
    sr = spearmanr(v, ps_mse)
    corr[k] = {"pearson_r": float(pr.statistic), "pearson_p": float(pr.pvalue),
               "spearman_rho": float(sr.statistic), "spearman_p": float(sr.pvalue)}

# 按 R_at_target 分位分箱看误差
qs = np.quantile(R_target, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
bins = []
for i in range(5):
    m = (R_target >= qs[i]) & (R_target <= qs[i + 1] if i == 4 else R_target < qs[i + 1])
    bins.append({"bin": i + 1, "R_lo": float(qs[i]), "R_hi": float(qs[i + 1]),
                 "n": int(m.sum()), "mse_mean": float(ps_mse[m].mean()),
                 "mae_mean": float(ps_mae[m].mean()), "maxabs_max": float(ps_max[m].max())})

# 失败案例候选
order = np.argsort(-ps_max)
worst = [{"rank": i + 1, "test_pos": int(o), "sample_index": int(idx_test[o]),
          "d_nm": D[o].tolist(), "per_sample_mse": float(ps_mse[o]),
          "per_sample_mae": float(ps_mae[o]), "per_sample_maxabs": float(ps_max[o]),
          "R_at_target_true": float(R_target[o]),
          "R_at_target_pred": float(pred[o, I_T]),
          "n_extrema": int(n_extrema[o]), "mean_abs_dR": float(fringe_mean[o]),
          "opt_thick_nm": float(opt_thick[o])}
         for i, o in enumerate(order[:8])]

# 命中率：预测值在真值附近的分位表现
out = {"n_test": int(len(idx_test)), "correlations_with_per_sample_mse": corr,
       "bins_by_R_at_target": bins, "worst_cases": worst,
       "notes": {"target_index": I_T, "target_nm": float(P.WAVELENGTHS[I_T])}}
(P.RES_DIR / "attribution.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"correlations": corr, "bins": bins}, ensure_ascii=False, indent=2))
print("\nworst 3:")
for w in worst[:3]:
    print(json.dumps(w, ensure_ascii=False))
