# -*- coding: utf-8 -*-
"""用不同容量的代理模型做同一筛选任务：精度提升能否转化为筛选能力？

3.5 节表明容量提升会把测试 MSE 降下来；但 Q3 关心的是"筛选"，不是"拟合"。
本脚本用完全相同的 10000 组候选、相同的 TMM 真值，只换代理模型，比较：
    base  4–128–128–64–41   测试 MSE 7.42e-5
    large 4–256–256–128–41  测试 MSE 3.12e-5
指标：目标波长处预测误差、排序一致性（Spearman/Pearson）、Top-k 召回率、
      Top1 是否为全批真值最优、预测值超过物理上限的个数。

输出 results/design_screen_capacity.json
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
N_TOP = 10

cand = np.load(P.DESIGN_NPZ)
D_des = cand["D"]
R_true = tmm.reflectance_char_matrix(D_des)
r_true = R_true[:, I_T]
order_true = np.argsort(-r_true)
bound = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))["R_bound"]

MODELS = {
    "base": (P.HIDDEN, P.RES_DIR / "model_base.pt"),
    "large": ((256, 256, 128), P.RES_DIR / "model_cap_large.pt"),
}

out = {"target_nm": float(P.LAMBDA_TARGET), "n_candidates": int(D_des.shape[0]),
       "R_physical_bound": bound, "models": {}}

for name, (hidden, path) in MODELS.items():
    ck = torch.load(path, weights_only=False)
    model = MLP(hidden)
    model.load_state_dict(ck["state"])
    model.eval()
    with torch.no_grad():
        pred = model(torch.tensor(scale_d(D_des), dtype=torch.float32)).numpy()
    r_pred = pred[:, I_T]
    order = np.argsort(-r_pred)
    top = order[:N_TOP]
    top_true_set = set(order_true[:N_TOP].tolist())
    recall = len(set(top.tolist()) & top_true_set) / N_TOP
    sp = spearmanr(r_pred, r_true)
    n_param = int(sum(p.numel() for p in model.parameters()))
    out["models"][name] = {
        "hidden": list(hidden),
        "n_param": n_param,
        "pred_mae_at_target": float(np.mean(np.abs(r_pred - r_true))),
        "pred_maxabs_at_target": float(np.max(np.abs(r_pred - r_true))),
        "spearman_rho": float(sp.statistic),
        "pearson_r": float(np.corrcoef(r_pred, r_true)[0, 1]),
        "top10_recall_vs_tmm_top10": float(recall),
        "top1_is_pool_best": bool(order[0] == order_true[0]),
        "top1_true_R": float(r_true[order[0]]),
        "top10_true_R_max": float(r_true[top].max()),
        "top10_true_R_mean": float(r_true[top].mean()),
        "n_pred_above_bound": int((r_pred > bound).sum()),
        "rank_of_true_best_under_model": int(np.where(order == order_true[0])[0][0]) + 1,
    }
    print(f"[{name}] MAE {out['models'][name]['pred_mae_at_target']:.5f}  "
          f"rho {sp.statistic:.5f}  top10召回 {recall:.0%}  "
          f"Top1即全批最优 {out['models'][name]['top1_is_pool_best']}  "
          f"真实最优的名次 {out['models'][name]['rank_of_true_best_under_model']}")

(P.RES_DIR / "design_screen_capacity.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten:", P.RES_DIR / "design_screen_capacity.json")
