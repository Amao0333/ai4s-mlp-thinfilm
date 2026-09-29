# -*- coding: utf-8 -*-
"""误差归因（覆盖度）：测试样本到训练集的最近邻距离能否解释误差？

在归一化的四维膜厚空间中计算每个测试样本到训练池的 k-近邻距离，
与逐样本误差做相关分析。若相关显著，则失败机理是"局部采样不足"，
也正好解释补充实验中局部加密为何有效。
输出 results/coverage.json
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import pearsonr, spearmanr

import params as P

d = np.load(P.DATA_NPZ)
D = (d["D"] - P.D_MIN) / (P.D_MAX - P.D_MIN)
idx_train, idx_test = d["idx_train"], d["idx_test"]
ev = np.load(P.RES_DIR / "base_eval.npz")
ps_mse, ps_mae = ev["per_sample_mse"], ev["per_sample_mae"]

Xtr, Xte = D[idx_train], D[idx_test]
# 逐块计算距离矩阵，避免一次性占用过多内存
K = 10
knn = np.empty((Xte.shape[0], K))
CH = 100
for i in range(0, Xte.shape[0], CH):
    blk = Xte[i:i + CH]
    dist = np.sqrt(((blk[:, None, :] - Xtr[None, :, :]) ** 2).sum(-1))
    knn[i:i + CH] = np.sort(dist, axis=1)[:, :K]

feats = {"d1": knn[:, 0], "d5": knn[:, 4], "d10": knn[:, 9]}
corr = {}
for k, v in feats.items():
    pr = pearsonr(v, ps_mse)
    sr = spearmanr(v, ps_mse)
    corr[k] = {"pearson_r": float(pr.statistic), "pearson_r2": float(pr.statistic ** 2),
               "pearson_p": float(pr.pvalue), "spearman_rho": float(sr.statistic)}

# 按最近邻距离分箱看误差
q = np.quantile(knn[:, 4], [0, 0.25, 0.5, 0.75, 1.0])
bins = []
for i in range(4):
    m = (knn[:, 4] >= q[i]) & (knn[:, 4] <= q[i + 1] if i == 3 else knn[:, 4] < q[i + 1])
    bins.append({"quartile": i + 1, "d5_lo": float(q[i]), "d5_hi": float(q[i + 1]),
                 "n": int(m.sum()), "mse_mean": float(ps_mse[m].mean()),
                 "mae_mean": float(ps_mae[m].mean())})

# 最差样本的覆盖情况对比
order = np.argsort(-ps_mse)
worst_idx = order[:25]
rest_idx = order[-25:]
np.savez_compressed(P.RES_DIR / "coverage.npz",
                    d1=knn[:, 0], d5=knn[:, 4], d10=knn[:, 9],
                    ps_mse=ps_mse, ps_mae=ps_mae)

out = {
    "distance_units": "归一化膜厚空间（每层除以 140 nm）中的欧氏距离",
    "correlations_with_per_sample_mse": corr,
    "bins_by_d5": bins,
    "worst25_mean_d5": float(knn[worst_idx, 4].mean()),
    "best25_mean_d5": float(knn[rest_idx, 4].mean()),
    "all_mean_d5": float(knn[:, 4].mean()),
    "ratio_worst_over_all": float(knn[worst_idx, 4].mean() / knn[:, 4].mean()),
}
(P.RES_DIR / "coverage.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
