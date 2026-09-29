# -*- coding: utf-8 -*-
"""补充实验：在损失函数中对 λtarget 加权，检验筛选能力是否提升。

对照：基础模型（41 点等权）vs 加权模型（λtarget 处权重 10，其余 1）。
在同一测试集与同一候选池上比较目标波长精度与排名一致性。
输出 results/weighted_loss.json
"""
from __future__ import annotations

import json
import time

import numpy as np
import torch
import torch.nn as nn
from scipy.stats import spearmanr

import params as P
import tmm
from model import MLP, scale_d

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
WEIGHT = 10.0


def train_weighted(n_train, seed, tag, weight):
    d = np.load(P.DATA_NPZ)
    D, R = d["D"], d["R"]
    idx_tr = d["idx_train"][:n_train]
    idx_va, idx_te = d["idx_val"], d["idx_test"]
    Xtr = torch.tensor(scale_d(D[idx_tr]), dtype=torch.float32)
    Ytr = torch.tensor(R[idx_tr], dtype=torch.float32)
    Xva = torch.tensor(scale_d(D[idx_va]), dtype=torch.float32)
    Yva = torch.tensor(R[idx_va], dtype=torch.float32)

    w = torch.ones(P.N_WL)
    w[I_T] = weight

    torch.manual_seed(seed)
    model = MLP(P.HIDDEN)
    opt = torch.optim.Adam(model.parameters(), lr=P.LR)
    gen = torch.Generator().manual_seed(seed)
    n = int(Xtr.shape[0])
    best = {"val": float("inf"), "epoch": -1, "state": None}
    t0 = time.perf_counter()
    for epoch in range(1, P.N_EPOCHS + 1):
        model.train()
        perm = torch.randperm(n, generator=gen)
        for i in range(0, n, P.BATCH_SIZE):
            b = perm[i:i + P.BATCH_SIZE]
            opt.zero_grad()
            loss = (((model(Xtr[b]) - Ytr[b]) ** 2) * w).mean()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vl = float((((model(Xva) - Yva) ** 2) * w).mean())
        if vl < best["val"]:
            best = {"val": vl, "epoch": epoch,
                    "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
        if epoch - best["epoch"] >= P.PATIENCE:
            break
    model.load_state_dict(best["state"])
    model.eval()
    torch.save({"state": best["state"], "tag": tag, "n_train": int(n), "init_seed": int(seed)},
               P.RES_DIR / f"model_{tag}.pt")
    return model, best, time.perf_counter() - t0


def evaluate(model, D_des, r_true_t):
    with torch.no_grad():
        R_mlp = model(torch.tensor(scale_d(D_des), dtype=torch.float32)).numpy()
    r_mlp_t = R_mlp[:, I_T]
    order_mlp = np.argsort(-r_mlp_t)
    order_true = np.argsort(-r_true_t)
    rho = spearmanr(r_mlp_t, r_true_t)
    return {
        "spearman_rho": float(rho.statistic),
        "mae_at_target": float(np.mean(np.abs(r_mlp_t - r_true_t))),
        "top1_is_tmm_best": bool(order_mlp[0] == order_true[0]),
        "top10_recall": float(len(set(order_mlp[:10]) & set(order_true[:10])) / 10.0),
        "best_of_mlp_top10_tmm": float(max(r_true_t[i] for i in order_mlp[:10])),
        "R_pool_best": float(r_true_t.max()),
        "n_pred_above_bound": int((r_mlp_t > 0.6588868299017764).sum()),
    }, R_mlp


d = np.load(P.RES_DIR / "design_screening.npz")
D_des, r_true_t = d["D_des"], d["r_true_target"]

model_w, best, dt = train_weighted(P.N_TRAIN, P.SEED, "weighted", WEIGHT)
res_w, R_mlp_w = evaluate(model_w, D_des, r_true_t)

base = MLP(P.HIDDEN)
base.load_state_dict(torch.load(P.RES_DIR / "model_base.pt", weights_only=False)["state"])
base.eval()
res_b, R_mlp_b = evaluate(base, D_des, r_true_t)

# 测试集上的目标波长精度
d2 = np.load(P.DATA_NPZ)
Dte, Rte = d2["D"][d2["idx_test"]], d2["R"][d2["idx_test"]]


def test_metrics(model):
    with torch.no_grad():
        pred = model(torch.tensor(scale_d(Dte), dtype=torch.float32)).numpy()
    err = pred - Rte
    return {"overall_mae": float(np.mean(np.abs(err))),
            "mae_at_target": float(np.mean(np.abs(err[:, I_T]))),
            "max_abs_at_target": float(np.max(np.abs(err[:, I_T])))}


out = {
    "design": {"weight_at_target": WEIGHT, "n_train": P.N_TRAIN, "seed": P.SEED,
               "epochs_run": best["epoch"], "wall_seconds": dt},
    "test_set": {"base": test_metrics(base), "weighted": test_metrics(model_w)},
    "candidate_pool": {"base": res_b, "weighted": res_w},
}
(P.RES_DIR / "weighted_loss.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
