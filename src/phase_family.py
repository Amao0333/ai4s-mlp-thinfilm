# -*- coding: utf-8 -*-
"""π 相位对称性：δ → δ + π 不改变反射率，故 λtarget 处的最优解是一个膜厚家族。

单层特征矩阵满足 M(δ+π) = −M(δ)，整体矩阵只差一个全局符号，
而 R 只依赖 C/B，符号自动抵消 —— 因此任意子集的层加上半个波长的光学厚度，光谱不变。
"""
from __future__ import annotations

import json

import numpy as np

import params as P
import tmm

I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))
WL_T = [float(P.WAVELENGTHS[I_T])]

n_seq = [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]
d_qw = [tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in n_seq]
half = [P.LAMBDA_TARGET / (2 * n) for n in n_seq]      # 半波长对应的物理厚度

# 四个家族成员：两片 H 层各自可选 QW 或 QW + λ/2（L 层加 λ/2 会超出 180 nm 上限）
members = []
for s1 in (0, 1):
    for s3 in (0, 1):
        d = [d_qw[0] + s1 * half[0], d_qw[1], d_qw[2] + s3 * half[2], d_qw[3]]
        if all(P.D_MIN <= x <= P.D_MAX for x in d):
            members.append({"shifts_H1_H3": [s1, s3], "d_nm": d,
                            "R_target": float(tmm.reflectance_char_matrix(d, WL_T)[0, 0])})

# 对照：随机扰动 0.5 nm 后 R 的下降，说明最优点的平坦度
rng = np.random.RandomState(P.SEED)
base = members[0]["d_nm"]
pert = np.array(base)[None, :] + rng.normal(0, 0.5, size=(2000, 4))
R_pert = tmm.reflectance_char_matrix(np.clip(pert, P.D_MIN, P.D_MAX), WL_T)[:, 0]

# λ/2 的物理厚度与盒约束检查
out = {
    "halfwave_thickness_nm": half,
    "in_box": [bool(P.D_MIN <= x <= P.D_MAX) for x in half],
    "family_members": members,
    "R_spread_within_family": float(np.ptp([m["R_target"] for m in members])),
    "perturbation_0p5nm": {"mean_R": float(R_pert.mean()), "min_R": float(R_pert.min()),
                           "mean_drop": float(R_pert.mean() - members[0]["R_target"])},
    "note": "四分之一波长解与 +λ/2 解在 λtarget 处完全等价（相位相差 π）",
}
(P.RES_DIR / "phase_family.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
