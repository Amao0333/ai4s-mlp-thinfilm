# -*- coding: utf-8 -*-
"""第 7 步：480 nm 的四分之一波长参考膜系与解析反射率。"""
from __future__ import annotations

import json

import numpy as np

import params as P
import tmm

n_seq = [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]
d_qw = [tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in n_seq]
chain = tmm.admittance_chain_qw(P.LAMBDA_TARGET, n_seq)
Y = chain[-1]
R_analytic = ((P.N_INCIDENT - Y) / (P.N_INCIDENT + Y)) ** 2
R_tmm = float(tmm.reflectance_char_matrix(d_qw, [P.LAMBDA_TARGET])[0, 0])
spec = tmm.reflectance_char_matrix(d_qw)[0]

out = {
    "stack": ["Air", "H", "L", "H", "L", "Glass"],
    "indices": {"H": P.N_HIGH, "L": P.N_LOW, "substrate": P.N_SUBSTRATE},
    "design_wavelength_nm": float(P.LAMBDA_TARGET),
    "thickness_nm": d_qw,
    "quarter_wave_condition_in_box": all(P.D_MIN <= x <= P.D_MAX for x in d_qw),
    "admittance_chain": chain,
    "R_analytic": R_analytic,
    "R_tmm": R_tmm,
    "abs_err": abs(R_analytic - R_tmm),
    "spectrum_R": spec.tolist(),
    "wavelengths": P.WAVELENGTHS.tolist(),
}
(P.RES_DIR / "qw_reference.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2)[:1200])
