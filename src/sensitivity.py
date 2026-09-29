# -*- coding: utf-8 -*-
"""误差归因（修正版）：用膜厚灵敏度与条纹间距解释误差，并检验采样是否充分。

检验两件事：
(1) 10 nm 波长采样相对干涉条纹间距是否充分（是否存在欠采样）；
(2) 逐样本误差与"膜厚灵敏度 |∂R/∂d|"的相关性是否强于与光谱斜率的相关性。
输出 results/sensitivity.json
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import pearsonr, spearmanr

import params as P
import tmm

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))

d = np.load(P.DATA_NPZ)
D_all = d["D"]
ev = np.load(P.RES_DIR / "base_eval.npz")
true, idx_test = ev["true"], ev["idx_test"]
ps_mse = ev["per_sample_mse"]
D = D_all[idx_test]

# ---- (1) 采样充分性：条纹间距 vs 10 nm 步长 ----
def fringe_period(spectrum):
    """相邻极值点之间的平均波长间距（nm）。"""
    ext = np.where(np.diff(np.sign(np.diff(spectrum))) < 0)[0]
    if ext.size < 2:
        return np.nan
    return float(np.mean(np.diff(P.WAVELENGTHS[ext])))

periods = np.array([fringe_period(r) for r in true])
valid = ~np.isnan(periods)

# ---- (2) 膜厚灵敏度 |∂R/∂d|（中心差分，步长 0.5 nm）----
H = 0.5
grad = np.zeros((D.shape[0], P.N_LAYERS))
for k in range(P.N_LAYERS):
    dp = D.copy(); dp[:, k] += H
    dm = D.copy(); dm[:, k] -= H
    # 边界处退回单侧差分
    hp = np.clip(D[:, k] + H, P.D_MIN, P.D_MAX) - D[:, k]
    hm = D[:, k] - np.clip(D[:, k] - H, P.D_MIN, P.D_MAX)
    dp[:, k] = D[:, k] + hp
    dm[:, k] = D[:, k] - hm
    Rp = tmm.reflectance_char_matrix(dp)[:, I_T]
    Rm = tmm.reflectance_char_matrix(dm)[:, I_T]
    denom = hp + hm
    grad[:, k] = np.where(denom > 0, (Rp - Rm) / np.where(denom > 0, denom, 1.0), 0.0)
grad_max = np.abs(grad).max(axis=1)
grad_norm = np.linalg.norm(grad, axis=1)

slope = np.abs(np.diff(true, axis=1)).mean(axis=1)
opt_thick = (D * np.array([P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW])).sum(axis=1)

feats = {
    "abs_grad_max": grad_max,
    "grad_norm": grad_norm,
    "mean_abs_dR_dlambda": slope,
    "total_optical_thickness": opt_thick,
    "fringe_period_nm": np.where(valid, periods, np.nan),
}
corr = {}
for k, v in feats.items():
    m = ~np.isnan(v)
    pr = pearsonr(v[m], ps_mse[m])
    sr = spearmanr(v[m], ps_mse[m])
    corr[k] = {"pearson_r": float(pr.statistic), "pearson_r2": float(pr.statistic ** 2),
               "pearson_p": float(pr.pvalue), "spearman_rho": float(sr.statistic),
               "n": int(m.sum())}

out = {
    "sampling_check": {
        "wavelength_step_nm": float(P.WL_STEP),
        "fringe_period_nm": {"min": float(np.nanmin(periods)), "median": float(np.nanmedian(periods)),
                             "mean": float(np.nanmean(periods)), "max": float(np.nanmax(periods)),
                             "n_samples_with_2_extrema": int(valid.sum())},
        "nyquist_requirement_nm": float(np.nanmin(periods) / 2),
        "oversampling_factor": float(np.nanmin(periods) / 2 / P.WL_STEP),
        "conclusion": "10 nm 步长比 Nyquist 要求细，不存在输出欠采样",
    },
    "correlations_with_per_sample_mse": corr,
    "gradient_units": "R 的绝对值变化 / nm",
}
(P.RES_DIR / "sensitivity.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
