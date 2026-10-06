# -*- coding: utf-8 -*-
"""第 14-16 步：MLP 辅助设计。

1) 用 design_seed 生成 10000 组候选膜厚（legacy 随机 API）
2) MLP 预测 41 点光谱，按 lambda_target 处 R 排序取 Top10
3) 全批 10000 组用 TMM 复核，量化排名一致性（Spearman）与 Top-10 召回率
4) MLP Top10 按 TMM 真值重排，取最终 Top5

输出 results/design_screening.json, data/design_candidates.npz
"""
from __future__ import annotations

import json

import numpy as np
import torch
from scipy.stats import spearmanr

import params as P
import tmm
from model import MLP, scale_d

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))

# ---- 1) 候选生成（legacy API + design_seed）----
np.random.seed(P.DESIGN_SEED)
D_des = P.D_MIN + (P.D_MAX - P.D_MIN) * np.random.rand(P.N_DESIGN, P.N_LAYERS)
np.savez_compressed(P.DESIGN_NPZ, D=D_des, design_seed=np.array([P.DESIGN_SEED]))

# ---- 2) MLP 预测与排序 ----
ckpt = torch.load(P.RES_DIR / "model_base.pt", weights_only=False)
model = MLP(P.HIDDEN)
model.load_state_dict(ckpt["state"])
model.eval()
with torch.no_grad():
    R_mlp = model(torch.tensor(scale_d(D_des), dtype=torch.float32)).numpy()

# ---- 3) TMM 复核全部候选 ----
R_true = tmm.reflectance_char_matrix(D_des)

r_mlp_t = R_mlp[:, I_T]
r_true_t = R_true[:, I_T]

order_mlp = np.argsort(-r_mlp_t)
order_true = np.argsort(-r_true_t)
top10_mlp = order_mlp[:10]
top10_true = order_true[:10]
top5_true = order_true[:5]

sp = spearmanr(r_mlp_t, r_true_t)
recall10 = float(len(set(top10_mlp.tolist()) & set(top10_true.tolist())) / 10.0)
recall5 = float(len(set(top10_mlp.tolist()) & set(top5_true.tolist())) / 5.0)

# MLP Top10 用 TMM 真值重排 -> 最终 Top5
verified = [{"rank_mlp": int(i + 1), "sample_index": int(o),
             "d_nm": D_des[o].tolist(),
             "R_mlp_target": float(r_mlp_t[o]),
             "R_tmm_target": float(r_true_t[o]),
             "percentile_tmm": float(100.0 * (r_true_t < r_true_t[o]).mean())}
            for i, o in enumerate(top10_mlp)]
final5 = sorted(verified, key=lambda x: -x["R_tmm_target"])[:5]
for i, f in enumerate(final5):
    f["final_rank"] = i + 1

R_best = float(r_true_t.max())
# 物理上限取自第 8 步的全局优化结果文件，避免在代码中重复写常数
R_bound = float(json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))["R_bound"])
p95 = float(np.percentile(r_true_t, 95))
p99 = float(np.percentile(r_true_t, 99))

out = {
    "design_seed": P.DESIGN_SEED,
    "n_candidates": int(D_des.shape[0]),
    "target_nm": float(P.WAVELENGTHS[I_T]),
    "ranking": {
        "spearman_rho": float(sp.statistic), "spearman_p": float(sp.pvalue),
        "pearson_r": float(np.corrcoef(r_mlp_t, r_true_t)[0, 1]),
        "top10_recall_vs_tmm_top10": recall10,
        "top5_recall_vs_tmm_top5": recall5,
        "n_mlp_top10_inside_tmm_top100": int(
            np.isin(top10_mlp, order_true[:100]).sum()),
    },
    "prediction_at_target": {
        "mae": float(np.mean(np.abs(r_mlp_t - r_true_t))),
        "rmse": float(np.sqrt(np.mean((r_mlp_t - r_true_t) ** 2))),
        "max_abs": float(np.max(np.abs(r_mlp_t - r_true_t))),
        "bias": float(np.mean(r_mlp_t - r_true_t)),
    },
    "pool_reference": {"R_best_tmm": R_best, "p95": p95, "p99": p99,
                       "R_physical_bound": R_bound},
    "mlp_top10_verified": verified,
    "final_top5": final5,
    "best_of_pool": {"sample_index": int(order_true[0]), "d_nm": D_des[order_true[0]].tolist(),
                     "R_tmm_target": R_best},
    "mlp_top1": {"sample_index": int(top10_mlp[0]), "d_nm": D_des[top10_mlp[0]].tolist(),
                 "R_mlp_target": float(r_mlp_t[top10_mlp[0]]),
                 "R_tmm_target": float(r_true_t[top10_mlp[0]])},
}
np.savez_compressed(P.RES_DIR / "design_screening.npz",
                    D_des=D_des, R_mlp=R_mlp, R_true=R_true,
                    r_mlp_target=r_mlp_t, r_true_target=r_true_t,
                    order_mlp=order_mlp, order_true=order_true)
(P.RES_DIR / "design_screening.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({k: out[k] for k in
                  ["ranking", "prediction_at_target", "pool_reference",
                   "best_of_pool", "mlp_top1"]}, ensure_ascii=False, indent=2))
print("\nfinal top5:")
for f in final5:
    print(json.dumps(f, ensure_ascii=False))
