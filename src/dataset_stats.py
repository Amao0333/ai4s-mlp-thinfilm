# -*- coding: utf-8 -*-
"""第 6 步：数据集统计 —— 重点看 lambda_target 处 R 的分布与高反射尾部覆盖。"""
from __future__ import annotations

import json

import numpy as np

import params as P

d = np.load(P.DATA_NPZ)
D, R, idx_train, idx_val, idx_test = d["D"], d["R"], d["idx_train"], d["idx_val"], d["idx_test"]

i_t = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
R_t = R[:, i_t]

# 高反射尾部覆盖
thr = [0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
cover_all = {f"{t:.2f}": int((R_t >= t).sum()) for t in thr}
cover_train = {f"{t:.2f}": int((R_t[idx_train] >= t).sum()) for t in thr}

# 条纹密度：对 41 点光谱做离散一阶差分的平均绝对值；及局部极大值个数
dR = np.abs(np.diff(R, axis=1))
fringe_mean = dR.mean(axis=1)
d2 = np.diff(R, axis=1)
sign = np.sign(d2)
n_extrema = np.sum((sign[:, 1:] * sign[:, :-1]) < 0, axis=1)
opt_thickness = (D * np.array([P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW])).sum(axis=1)

hist_counts, hist_edges = np.histogram(R_t, bins=40, range=(0.0, 0.7))

out = {
    "n_total": int(R.shape[0]),
    "wavelength_of_target_nm": float(P.WAVELENGTHS[i_t]),
    "R_at_target": {
        "all_5000": {"min": float(R_t.min()), "max": float(R_t.max()),
                     "mean": float(R_t.mean()), "std": float(R_t.std()),
                     "median": float(np.median(R_t)),
                     "p99": float(np.percentile(R_t, 99)),
                     "p999": float(np.percentile(R_t, 99.9))},
        "train_pool": {"min": float(R_t[idx_train].min()), "max": float(R_t[idx_train].max()),
                       "mean": float(R_t[idx_train].mean())},
    },
    "count_R_above_threshold_all": cover_all,
    "count_R_above_threshold_train_pool": cover_train,
    "fringe_metric": {
        "mean_abs_dR_per_10nm": {"min": float(fringe_mean.min()),
                                 "mean": float(fringe_mean.mean()),
                                 "max": float(fringe_mean.max())},
        "n_local_extrema": {"min": int(n_extrema.min()), "mean": float(n_extrema.mean()),
                            "max": int(n_extrema.max())},
    },
    "total_optical_thickness_nm": {"min": float(opt_thickness.min()),
                                   "mean": float(opt_thickness.mean()),
                                   "max": float(opt_thickness.max())},
    "hist_R_at_target": {"counts": hist_counts.tolist(), "edges": hist_edges.tolist()},
    "R_overall": {"min": float(R.min()), "max": float(R.max())},
}
(P.RES_DIR / "dataset_stats.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
