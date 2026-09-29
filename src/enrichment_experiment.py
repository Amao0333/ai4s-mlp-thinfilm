# -*- coding: utf-8 -*-
"""第 18 步（补充实验）：在高反射区局部加密采样，检验该区域精度是否提升。

设计（干净对照，样本总数不变）：
  A 组 = 训练池前 4000 组（原方案，已有 model_base.pt）
  B 组 = 训练池前 3500 组 + 500 组四分之一波长附近的加密样本（共 4000 组）
评价：
  标准测试集（500 组）与高反射测试集（200 组，QW 附近 sigma=15 nm，独立生成）
输出 results/enrichment_experiment.json
"""
from __future__ import annotations

import json

import numpy as np
import torch

import params as P
import tmm
from model import MLP, scale_d
from train import train_idx

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
N_ENRICH = 500
SIGMA_ENRICH = 15.0
N_HR_TEST = 200

d = np.load(P.DATA_NPZ)
D, R = d["D"], d["R"]
idx_train, idx_val, idx_test = d["idx_train"], d["idx_val"], d["idx_test"]


def near_qw(n, sigma, seed):
    """在四分之一波长解附近采样，裁到 40-180 nm。"""
    d_qw = np.array([tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in
                     [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]])
    rng = np.random.RandomState(seed)
    return np.clip(d_qw[None, :] + rng.normal(0.0, sigma, size=(n, P.N_LAYERS)),
                   P.D_MIN, P.D_MAX)


D_enr = near_qw(N_ENRICH, SIGMA_ENRICH, P.SEED + 5)
R_enr = tmm.reflectance_char_matrix(D_enr)

D_hr = near_qw(N_HR_TEST, SIGMA_ENRICH, P.SEED + 7)
R_hr = tmm.reflectance_char_matrix(D_hr)

D_ext = np.vstack([D, D_enr])
R_ext = np.vstack([R, R_enr])
idx_b = np.concatenate([idx_train[:3500], np.arange(P.N_TOTAL, P.N_TOTAL + N_ENRICH)])

out = train_idx(D_ext, R_ext, idx_b, idx_val, idx_test, P.SEED, "enriched")


def evaluate(state_path, D_eval, R_eval):
    ck = torch.load(state_path, weights_only=False)
    m = MLP(P.HIDDEN)
    m.load_state_dict(ck["state"])
    m.eval()
    with torch.no_grad():
        pr = m(torch.tensor(scale_d(D_eval), dtype=torch.float32)).numpy()
    err = pr - R_eval
    return {
        "mse": float(np.mean(err ** 2)), "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mae_at_target": float(np.mean(np.abs(err[:, I_T]))),
        "rmse_at_target": float(np.sqrt(np.mean(err[:, I_T] ** 2))),
        "max_abs": float(np.max(np.abs(err))),
    }


res = {
    "design": {"n_enrich": N_ENRICH, "sigma_nm": SIGMA_ENRICH, "n_hr_test": N_HR_TEST,
               "group_A": "训练池前 4000 组（原方案）",
               "group_B": "训练池前 3500 组 + 500 组 QW 附近加密样本",
               "enrich_seed": P.SEED + 5, "hr_test_seed": P.SEED + 7},
    "group_A": {"standard_test": evaluate(P.RES_DIR / "model_base.pt", D[idx_test], R[idx_test]),
                "high_R_test": evaluate(P.RES_DIR / "model_base.pt", D_hr, R_hr)},
    "group_B": {"standard_test": evaluate(P.RES_DIR / "model_enriched.pt", D[idx_test], R[idx_test]),
                "high_R_test": evaluate(P.RES_DIR / "model_enriched.pt", D_hr, R_hr),
                "train_metrics": out["test"]},
    "high_R_test_set": {"R_at_target_min": float(R_hr[:, I_T].min()),
                        "R_at_target_mean": float(R_hr[:, I_T].mean()),
                        "R_at_target_max": float(R_hr[:, I_T].max())},
}
for key in ("standard_test", "high_R_test"):
    a = res["group_A"][key]["mse"]
    b = res["group_B"][key]["mse"]
    res.setdefault("comparison", {})[key] = {
        "mse_A": a, "mse_B": b, "relative_change": (b - a) / a}
(P.RES_DIR / "enrichment_experiment.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=2))
