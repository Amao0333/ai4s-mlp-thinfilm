# -*- coding: utf-8 -*-
"""第 19 步：最终设计的厚度公差敏感性分析。

两类误差：系统性整体缩放误差（镀膜速率偏差）与逐层随机误差（Monte Carlo）。
输出 results/tolerance.json
"""
from __future__ import annotations

import json

import numpy as np

import params as P
import tmm

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
ds = json.loads((P.RES_DIR / "design_screening.json").read_text(encoding="utf-8"))
d_star = np.array(ds["final_top5"][0]["d_nm"], dtype=float)
R0 = float(tmm.reflectance_char_matrix(d_star, [P.LAMBDA_TARGET])[0, 0])

scale_rows = []
for eps in [-0.05, -0.03, -0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02, 0.03, 0.05]:
    d = d_star * (1.0 + eps)
    if not np.all((d >= P.D_MIN) & (d <= P.D_MAX)):
        R = float(tmm.reflectance_char_matrix(np.clip(d, P.D_MIN, P.D_MAX), [P.LAMBDA_TARGET])[0, 0])
        clipped = True
    else:
        R = float(tmm.reflectance_char_matrix(d, [P.LAMBDA_TARGET])[0, 0])
        clipped = False
    scale_rows.append({"eps": eps, "R_target": R, "dR": R - R0, "clipped": clipped})

rng = np.random.RandomState(P.SEED)
mc_rows = []
for sigma in [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]:
    draws = d_star[None, :] + rng.normal(0.0, sigma, size=(2000, P.N_LAYERS))
    draws = np.clip(draws, P.D_MIN, P.D_MAX)
    R = tmm.reflectance_char_matrix(draws)[:, I_T]
    mc_rows.append({"sigma_nm": sigma, "mean_R": float(R.mean()), "std_R": float(R.std()),
                    "p01": float(np.percentile(R, 1)), "p50": float(np.percentile(R, 50)),
                    "min_R": float(R.min()), "mean_dR": float(R.mean() - R0),
                    "worst_dR": float(R.min() - R0)})

out = {
    "design": d_star.tolist(), "R_target_reference": R0,
    "target_nm": float(P.WAVELENGTHS[I_T]),
    "systematic_scale": scale_rows,
    "monte_carlo_per_layer": mc_rows,
    "n_mc": 2000,
}
(P.RES_DIR / "tolerance.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
