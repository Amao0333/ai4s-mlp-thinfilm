# -*- coding: utf-8 -*-
"""第 10 步：在固定测试集上评估基础模型，导出逐波长与逐样本误差。

输出 results/base_eval.npz 与 results/base_eval.json
"""
from __future__ import annotations

import json

import numpy as np
import torch

import params as P
from model import MLP, scale_d

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))

d = np.load(P.DATA_NPZ)
D, R = d["D"], d["R"]
idx_te = d["idx_test"]

ckpt = torch.load(P.RES_DIR / "model_base.pt", weights_only=False)
model = MLP(P.HIDDEN)
model.load_state_dict(ckpt["state"])
model.eval()

Xte = torch.tensor(scale_d(D[idx_te]), dtype=torch.float32)
with torch.no_grad():
    pred = model(Xte).numpy()
true = R[idx_te]

err = pred - true
per_wl_mae = np.mean(np.abs(err), axis=0)
per_wl_rmse = np.sqrt(np.mean(err ** 2, axis=0))
per_sample_mse = np.mean(err ** 2, axis=1)
per_sample_mae = np.mean(np.abs(err), axis=1)
per_sample_maxabs = np.max(np.abs(err), axis=1)

summary = {
    "n_test": int(len(idx_te)),
    "overall": {
        "mse": float(np.mean(err ** 2)), "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mae": float(np.mean(np.abs(err))), "max_abs": float(np.max(np.abs(err))),
        "r2": float(1 - np.sum(err ** 2) / np.sum((true - true.mean()) ** 2)),
    },
    "at_target": {
        "wavelength_nm": float(P.WAVELENGTHS[I_T]),
        "mae": float(np.mean(np.abs(err[:, I_T]))),
        "rmse": float(np.sqrt(np.mean(err[:, I_T] ** 2))),
        "max_abs": float(np.max(np.abs(err[:, I_T]))),
        "bias": float(np.mean(err[:, I_T])),
        "pearson_r": float(np.corrcoef(pred[:, I_T], true[:, I_T])[0, 1]),
    },
    "per_wavelength": {"mae": per_wl_mae.tolist(), "rmse": per_wl_rmse.tolist(),
                       "wavelengths": P.WAVELENGTHS.tolist()},
    "per_sample": {
        "mse_min": float(per_sample_mse.min()), "mse_median": float(np.median(per_sample_mse)),
        "mse_mean": float(per_sample_mse.mean()), "mse_max": float(per_sample_mse.max()),
        "mae_max": float(per_sample_mae.max()),
        "maxabs_max": float(per_sample_maxabs.max()),
    },
    "best_epoch": int(ckpt["best_epoch"]),
}

np.savez_compressed(P.RES_DIR / "base_eval.npz",
                    pred=pred, true=true, idx_test=idx_te,
                    per_sample_mse=per_sample_mse, per_sample_mae=per_sample_mae,
                    per_sample_maxabs=per_sample_maxabs,
                    per_wl_mae=per_wl_mae)
(P.RES_DIR / "base_eval.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
