# -*- coding: utf-8 -*-
"""第 8 步：在膜厚盒约束内求 lambda_target 处反射率的物理上限。

方法：差分进化（全局）+ 多起点 L-BFGS-B（局域精修），两者取较优。
"""
from __future__ import annotations

import json
import time

import numpy as np
from scipy.optimize import differential_evolution, minimize

import params as P
import tmm

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
WL_T = [float(P.WAVELENGTHS[I_T])]
BOUNDS = [(P.D_MIN, P.D_MAX)] * P.N_LAYERS


def neg_R(d):
    d = np.clip(np.asarray(d, dtype=float).reshape(1, -1), P.D_MIN, P.D_MAX)
    return -float(tmm.reflectance_char_matrix(d, WL_T)[0, 0])


t0 = time.perf_counter()
de = differential_evolution(neg_R, BOUNDS, seed=P.SEED, maxiter=400, popsize=25,
                            tol=1e-12, mutation=(0.3, 1.2), recombination=0.9,
                            polish=True, updating="deferred")
t_de = time.perf_counter() - t0

rng = np.random.RandomState(20260929)
starts = [de.x] + [rng.uniform(P.D_MIN, P.D_MAX, P.N_LAYERS) for _ in range(40)]
best_d, best_v, n_local = None, np.inf, 0
t0 = time.perf_counter()
for s in starts:
    r = minimize(neg_R, s, method="L-BFGS-B", bounds=BOUNDS,
                 options={"maxiter": 2000, "ftol": 1e-15, "gtol": 1e-12})
    n_local += 1
    if r.fun < best_v:
        best_v, best_d = float(r.fun), r.x.copy()
t_local = time.perf_counter() - t0

d_opt = np.clip(best_d, P.D_MIN, P.D_MAX)
R_opt = float(tmm.reflectance_char_matrix(d_opt, WL_T)[0, 0])
R_de = -float(de.fun)
d_de = np.clip(de.x, P.D_MIN, P.D_MAX)

n_seq = [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]
d_qw = [tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in n_seq]
R_qw = float(tmm.reflectance_char_matrix(d_qw, WL_T)[0, 0])

use_local = R_opt >= R_de
d_best = (d_opt if use_local else d_de).tolist()
out = {
    "target_nm": WL_T[0],
    "method": {"differential_evolution": {"maxiter": 400, "popsize": 25, "seed": P.SEED},
               "local_multistart": {"n_starts": n_local, "method": "L-BFGS-B"}},
    "R_bound": max(R_opt, R_de),
    "d_bound_nm": d_best,
    "bound_from": "local_multistart" if use_local else "differential_evolution",
    "R_local_multistart": R_opt,
    "d_local_multistart_nm": d_opt.tolist(),
    "R_differential_evolution": R_de,
    "d_differential_evolution_nm": d_de.tolist(),
    "R_quarter_wave": R_qw,
    "d_quarter_wave_nm": d_qw,
    "bound_minus_qw": max(R_opt, R_de) - R_qw,
    "time_seconds": {"differential_evolution": t_de, "local_multistart": t_local},
    "spectrum_of_bound": tmm.reflectance_char_matrix(d_best)[0].tolist(),
    "wavelengths": P.WAVELENGTHS.tolist(),
}
(P.RES_DIR / "physical_bound.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
