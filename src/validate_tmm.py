# -*- coding: utf-8 -*-
"""TMM 三级校核：解析参照 + 双实现互检 + 能量守恒。

输出 results/tmm_validation.json
"""
from __future__ import annotations

import json
import time

import numpy as np

import params as P
import tmm

out = {}

# ---- 1. 裸基底：解析 4.258% ----
exp_bare = tmm.reflectance_bare_substrate()
got_bare = float(tmm.reflectance_char_matrix(np.zeros((1, P.N_LAYERS)), [550.0])[0, 0])
out["bare_substrate"] = {"analytic": exp_bare, "tmm": got_bare,
                         "abs_err": abs(exp_bare - got_bare)}

# ---- 2. QW 膜系在 480 nm：导纳链解析 ----
n_seq = [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]        # Air 侧起
d_qw = np.array([tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in n_seq])
chain = tmm.admittance_chain_qw(P.LAMBDA_TARGET, n_seq)
Y_qw = chain[-1]
exp_qw = ((P.N_INCIDENT - Y_qw) / (P.N_INCIDENT + Y_qw)) ** 2
got_qw = float(tmm.reflectance_char_matrix(d_qw, [P.LAMBDA_TARGET])[0, 0])
out["quarter_wave_stack"] = {"thickness_nm": d_qw.tolist(),
                             "admittance_chain": chain,
                             "analytic_R": exp_qw, "tmm_R": got_qw,
                             "abs_err": abs(exp_qw - got_qw)}

# ---- 3. 单层膜解析式 ----
rng = np.random.RandomState(20260929)
errs = []
for _ in range(200):
    n1 = float(rng.uniform(1.2, 2.6))
    d1 = float(rng.uniform(20, 300))
    wl = float(rng.uniform(400, 800))
    exp = tmm.reflectance_single_layer(n1, d1, wl)
    got = float(tmm.reflectance_char_matrix([d1, 0, 0, 0], [wl],
                                            n_layer=[n1, 1.0, 1.0, 1.0])[0, 0])
    errs.append(abs(exp - got))
out["single_layer"] = {"n_cases": len(errs), "max_abs_err": float(np.max(errs))}

# ---- 4. 双实现互检 ----
d_rand = rng.uniform(P.D_MIN, P.D_MAX, size=(2000, P.N_LAYERS))
r_char = tmm.reflectance_char_matrix(d_rand)
r_imp = tmm.reflectance_impedance(d_rand)
out["two_implementations"] = {
    "n_samples": int(d_rand.shape[0]), "n_wavelengths": int(P.N_WL),
    "max_abs_diff": float(np.max(np.abs(r_char - r_imp))),
    "R_range": [float(r_char.min()), float(r_char.max())],
}

# ---- 5. 能量守恒 R + T = 1 ----
T = tmm.transmittance_char_matrix(d_rand)
out["energy_conservation"] = {"max_deviation": float(np.max(np.abs(r_char + T - 1.0)))}

# ---- 6. 5000 组规模耗时预估 ----
d_big = rng.uniform(P.D_MIN, P.D_MAX, size=(P.N_TOTAL, P.N_LAYERS))
t0 = time.perf_counter()
tmm.reflectance_char_matrix(d_big)
dt = time.perf_counter() - t0
out["timing"] = {"n_samples": P.N_TOTAL, "seconds": dt, "per_sample_us": dt / P.N_TOTAL * 1e6}
d_big2 = rng.uniform(P.D_MIN, P.D_MAX, size=(P.N_DESIGN, P.N_LAYERS))
t0 = time.perf_counter()
tmm.reflectance_char_matrix(d_big2)
dt2 = time.perf_counter() - t0
out["timing"]["n_design"] = P.N_DESIGN
out["timing"]["seconds_design"] = dt2

print(json.dumps(out, ensure_ascii=False, indent=2))
(P.RES_DIR / "tmm_validation.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten:", P.RES_DIR / "tmm_validation.json")
