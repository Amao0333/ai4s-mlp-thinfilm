# -*- coding: utf-8 -*-
"""第 17 步：MLP 代理模型与 TMM 的耗时基准与盈亏平衡规模。

输出 results/benchmark.json
"""
from __future__ import annotations

import json
import time

import numpy as np
import torch

import params as P
import tmm
from model import MLP, scale_d

d = np.load(P.RES_DIR / "design_screening.npz")
D_des = d["D_des"]
N = int(D_des.shape[0])

ckpt = torch.load(P.RES_DIR / "model_base.pt", weights_only=False)
model = MLP(P.HIDDEN)
model.load_state_dict(ckpt["state"])
model.eval()
X = torch.tensor(scale_d(D_des), dtype=torch.float32)

# 预热
tmm.reflectance_char_matrix(D_des[:16])
with torch.no_grad():
    model(X[:16])

# 计时取多次重复的中位数：单次测量在共享机器上波动可达数倍
reps = 9
_t = []
for _ in range(reps):
    t0 = time.perf_counter()
    tmm.reflectance_char_matrix(D_des)
    _t.append(time.perf_counter() - t0)
t_tmm = float(np.median(_t))

_t = []
with torch.no_grad():
    for _ in range(reps):
        t0 = time.perf_counter()
        model(X)
        _t.append(time.perf_counter() - t0)
t_mlp = float(np.median(_t))

# 单点前向（1 个候选）
_t = []
for _ in range(200):
    t0 = time.perf_counter()
    tmm.reflectance_char_matrix(D_des[:1])
    _t.append(time.perf_counter() - t0)
t_tmm_1 = float(np.median(_t))
_t = []
with torch.no_grad():
    for _ in range(200):
        t0 = time.perf_counter()
        model(X[:1])
        _t.append(time.perf_counter() - t0)
t_mlp_1 = float(np.median(_t))

train_time = json.loads((P.RES_DIR / "metrics_base.json").read_text(encoding="utf-8"))["wall_seconds"]

# 盈亏平衡：把训练开销摊到筛选上。
# 注意：t_tmm / t_mlp 是对 N 个候选的总耗时，需先换算成单候选的边际节省，
# 否则得到的是“需要多少个候选批次”而非候选数（早期版本在此处差了 N 倍）。
marginal_per_candidate = (t_tmm - t_mlp) / N
breakeven = train_time / marginal_per_candidate if marginal_per_candidate > 0 else None

# 实际设计流程耗时对比
t0 = time.perf_counter()
Rt = tmm.reflectance_char_matrix(D_des)
t_exhaustive = time.perf_counter() - t0
t0 = time.perf_counter()
with torch.no_grad():
    Rm = model(X).numpy()
order = np.argsort(-Rm[:, 8])[:10]
credits = tmm.reflectance_char_matrix(D_des[order])
t_surrogate = (time.perf_counter() - t0)

out = {
    "n_candidates": N,
    "tmm": {"batch_seconds": t_tmm, "per_candidate_us": t_tmm / N * 1e6,
            "single_call_us": t_tmm_1 * 1e6},
    "mlp": {"batch_seconds": t_mlp, "per_candidate_us": t_mlp / N * 1e6,
            "single_call_us": t_mlp_1 * 1e6},
    "speedup_batch": t_tmm / t_mlp,
    "speedup_single": t_tmm_1 / t_mlp_1,
    "training_seconds": train_time,
    "breakeven_candidates": breakeven,
    "design_workflow": {
        "exhaustive_tmm_seconds": t_exhaustive,
        "mlp_then_verify_top10_seconds": t_surrogate,
        "speedup": t_exhaustive / t_surrogate,
    },
    "note": "exhaustive = TMM on all candidates; surrogate = MLP on all + TMM on Top10",
}
(P.RES_DIR / "benchmark.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
