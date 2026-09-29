# -*- coding: utf-8 -*-
"""第 12 步：训练数据量实验（500/1000/2000/4000，各 3 个初始化种子）。

数据子集、超参数、验证集与测试集全部固定，只有训练样本数与初始化种子变化。
输出 results/size_experiment.json
"""
from __future__ import annotations

import json

import numpy as np

import params as P
from train import train

runs = []
for n in P.SIZE_LEVELS:
    for seed in P.TRAIN_SEEDS:
        tag = f"size{n}_s{seed}"
        out = train(n, seed, tag)
        runs.append({"n_train": int(n), "init_seed": int(seed), "tag": tag,
                     "epochs_run": out["epochs_run"], "best_epoch": out["best_epoch"],
                     "val_mse": out["val_mse_best"], "test": out["test"],
                     "wall_seconds": out["wall_seconds"]})

levels = []
for n in P.SIZE_LEVELS:
    sub = [r for r in runs if r["n_train"] == n]
    mse = np.array([r["test"]["mse"] for r in sub], dtype=float)
    mae = np.array([r["test"]["mae"] for r in sub], dtype=float)
    rmse = np.array([r["test"]["rmse"] for r in sub], dtype=float)
    levels.append({
        "n_train": int(n),
        "test_mse": mse.tolist(), "test_mse_mean": float(mse.mean()),
        "test_mse_std": float(mse.std(ddof=1)),
        "test_rmse_mean": float(rmse.mean()), "test_rmse_std": float(rmse.std(ddof=1)),
        "test_mae_mean": float(mae.mean()), "test_mae_std": float(mae.std(ddof=1)),
    })

# 幂律拟合：log(MSE) = log(a) - alpha * log(N)
N_arr = np.array([lv["n_train"] for lv in levels], dtype=float)
M_arr = np.array([lv["test_mse_mean"] for lv in levels], dtype=float)
slope, intercept = np.polyfit(np.log(N_arr), np.log(M_arr), 1)
pred = slope * np.log(N_arr) + intercept
ss_res = float(np.sum((np.log(M_arr) - pred) ** 2))
ss_tot = float(np.sum((np.log(M_arr) - np.log(M_arr).mean()) ** 2))
fit = {"alpha": float(-slope), "a": float(np.exp(intercept)),
       "r2": 1.0 - ss_res / ss_tot,
       "x": np.log(N_arr).tolist(), "y": np.log(M_arr).tolist(),
       "y_fit": pred.tolist()}

out = {"runs": runs, "levels": levels, "power_law_fit": fit,
       "hyperparams": {"optimizer": "Adam", "lr": P.LR, "batch_size": P.BATCH_SIZE,
                       "max_epochs": P.N_EPOCHS, "patience": P.PATIENCE,
                       "arch": [P.N_LAYERS, *P.HIDDEN, P.N_WL]}}
(P.RES_DIR / "size_experiment.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"levels": levels, "power_law_fit": fit}, ensure_ascii=False, indent=2))
