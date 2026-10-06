# -*- coding: utf-8 -*-
"""第 9 步：训练 MLP 代理模型（数据量实验复用同一函数）。

用法：py src/train.py [tag] [n_train] [seed]
默认：tag=base, n_train=4000, seed=params.SEED
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import torch
import torch.nn as nn

import params as P
from model import MLP, scale_d


def _tensors(D, R, idx):
    X = torch.tensor(scale_d(D[idx]), dtype=torch.float32)
    Y = torch.tensor(R[idx], dtype=torch.float32)
    return X, Y


def train(n_train, seed, tag="run", verbose=True):
    d = np.load(P.DATA_NPZ)
    D, R = d["D"], d["R"]
    idx_train = d["idx_train"][:n_train]
    idx_val, idx_test = d["idx_val"], d["idx_test"]
    return train_idx(D, R, idx_train, idx_val, idx_test, seed, tag, verbose)


def train_idx(D, R, idx_train, idx_val, idx_test, seed, tag="run", verbose=True, hidden=None):
    """在给定索引上训练，供数据量实验与补充实验复用。

    hidden=None 时用 params.HIDDEN（论文基准结构）；传入元组可做容量对照实验，
    除网络结构外其余超参数完全一致。
    """
    hidden = tuple(P.HIDDEN if hidden is None else hidden)
    torch.manual_seed(seed)
    Xtr, Ytr = _tensors(D, R, idx_train)
    Xva, Yva = _tensors(D, R, idx_val)
    Xte, Yte = _tensors(D, R, idx_test)

    model = MLP(hidden)
    opt = torch.optim.Adam(model.parameters(), lr=P.LR)
    lossf = nn.MSELoss()
    gen = torch.Generator().manual_seed(seed)
    n = int(Xtr.shape[0])

    best = {"val": float("inf"), "epoch": -1, "state": None, "train": None}
    hist = {"train": [], "val": []}
    t0 = time.perf_counter()
    for epoch in range(1, P.N_EPOCHS + 1):
        model.train()
        perm = torch.randperm(n, generator=gen)
        tot, cnt = 0.0, 0
        for i in range(0, n, P.BATCH_SIZE):
            b = perm[i:i + P.BATCH_SIZE]
            opt.zero_grad()
            loss = lossf(model(Xtr[b]), Ytr[b])
            loss.backward()
            opt.step()
            tot += float(loss.detach()) * int(b.numel())
            cnt += int(b.numel())
        tr = tot / cnt
        model.eval()
        with torch.no_grad():
            vl = float(lossf(model(Xva), Yva))
        hist["train"].append(tr)
        hist["val"].append(vl)
        if vl < best["val"]:
            best = {"val": vl, "epoch": epoch, "train": tr,
                    "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
        if epoch - best["epoch"] >= P.PATIENCE:
            break
    dt = time.perf_counter() - t0

    model.load_state_dict(best["state"])
    model.eval()
    with torch.no_grad():
        pred_te = model(Xte).numpy()
        pred_va = model(Xva).numpy()
    true_te, true_va = Yte.numpy(), Yva.numpy()

    def metrics(pred, true):
        err = pred - true
        mse = float(np.mean(err ** 2))
        mae = float(np.mean(np.abs(err)))
        ss_res = float(np.sum(err ** 2))
        ss_tot = float(np.sum((true - true.mean()) ** 2))
        return {"mse": mse, "rmse": float(np.sqrt(mse)), "mae": mae,
                "max_abs": float(np.max(np.abs(err))),
                "r2": 1.0 - ss_res / ss_tot}

    out = {
        "tag": tag, "n_train": int(len(idx_train)), "init_seed": int(seed),
        "epochs_run": len(hist["train"]), "best_epoch": best["epoch"],
        "history": hist,
        "val_mse_best": best["val"],
        "test": metrics(pred_te, true_te),
        "val": metrics(pred_va, true_va),
        "wall_seconds": dt,
        "arch": [P.N_LAYERS, *hidden, P.N_WL],
        "n_param": int(sum(p.numel() for p in model.parameters())),
    }
    torch.save({"state": best["state"], "tag": tag, "n_train": int(len(idx_train)),
                "init_seed": int(seed), "best_epoch": best["epoch"]},
               P.RES_DIR / f"model_{tag}.pt")
    (P.RES_DIR / f"metrics_{tag}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    if verbose:
        print(f"[{tag}] n_train={len(idx_train)} seed={seed} epochs={out['epochs_run']} "
              f"best={best['epoch']} val_mse={best['val']:.3e} "
              f"test_mse={out['test']['mse']:.3e} test_rmse={out['test']['rmse']:.3e} "
              f"test_mae={out['test']['mae']:.3e} ({dt:.1f}s)")
    return out


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "base"
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else P.N_TRAIN
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else P.SEED
    train(n_train, seed, tag)
