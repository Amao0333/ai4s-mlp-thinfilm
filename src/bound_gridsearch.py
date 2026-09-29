# -*- coding: utf-8 -*-
"""物理上限的独立确认：密集网格穷举 + 局部细化。

与 optimize_bound.py（差分进化 + 多起点局部优化）互为独立证据。
输出 results/physical_bound_grid.json
"""
from __future__ import annotations

import json
import time

import numpy as np

import params as P
import tmm

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
WL_T = [float(P.WAVELENGTHS[I_T])]
N_GRID = 41          # 每层 41 点（间隔 3.5 nm）
CHUNK = 200_000


def scan(lo, hi, n):
    """在 [lo, hi]^4 的四维网格上穷举 R(λtarget)，返回最优解与网格点总数。"""
    ax = np.linspace(lo, hi, n)
    total = 0
    best_r, best_d = -1.0, None
    for i in range(n):                       # 分块遍历，控制内存
        for j in range(n):
            g1, g2 = np.meshgrid(ax, ax, indexing="ij")
            d3, d4 = np.meshgrid(ax, ax, indexing="ij")
            D = np.stack([np.full(g1.size, ax[i]), np.full(g1.size, ax[j]),
                          g1.ravel(), g2.ravel()], axis=1)
            R = tmm.reflectance_char_matrix(D, WL_T)[:, 0]
            total += D.shape[0]
            k = int(np.argmax(R))
            if R[k] > best_r:
                best_r, best_d = float(R[k]), D[k].copy()
    return best_r, best_d, total


t0 = time.perf_counter()
r0, d0, n0 = scan(P.D_MIN, P.D_MAX, N_GRID)
t_coarse = time.perf_counter() - t0

# 局部细化：在粗网格最优解附近逐步缩小包围盒
lo, hi = d0.copy(), d0.copy()
r_best, d_best = r0, d0.copy()
hist = [{"stage": "coarse", "R": r0, "d": d0.tolist(), "n_points": n0}]
for k, span in enumerate([1.75, 0.44, 0.11]):
    lo_k = np.clip(d_best - span, P.D_MIN, P.D_MAX)
    hi_k = np.clip(d_best + span, P.D_MIN, P.D_MAX)
    grid = [np.linspace(lo_k[i], hi_k[i], 9) for i in range(4)]
    D = np.stack(np.meshgrid(*grid, indexing="ij"), axis=-1).reshape(-1, 4)
    R = tmm.reflectance_char_matrix(D, WL_T)[:, 0]
    k_best = int(np.argmax(R))
    if R[k_best] > r_best:
        r_best, d_best = float(R[k_best]), D[k_best].copy()
    hist.append({"stage": f"refine{span}", "R": r_best, "d": d_best.tolist(),
                 "n_points": int(D.shape[0])})
t_total = time.perf_counter() - t0

pb = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))
out = {
    "target_nm": WL_T[0],
    "grid_points_per_layer": N_GRID,
    "total_grid_evaluations": int(n0),
    "R_grid_best": r_best,
    "d_grid_best_nm": d_best.tolist(),
    "history": hist,
    "R_from_optimizer": pb["R_bound"],
    "R_quarter_wave": pb["R_quarter_wave"],
    "difference_vs_optimizer": abs(r_best - pb["R_bound"]),
    "time_seconds": {"coarse": t_coarse, "total": t_total},
}
(P.RES_DIR / "physical_bound_grid.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
