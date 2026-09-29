# -*- coding: utf-8 -*-
"""传输矩阵法（TMM）：两套独立实现。

主实现  reflectance_char_matrix()  —— 2x2 特征矩阵连乘
校验实现 reflectance_impedance()    —— 等效导纳递推
两者数学等价但代码路径完全不同，用于互相验错。

正入射、介质无吸收、忽略色散。导纳用自由空间单位：eta = n。
"""
from __future__ import annotations

import numpy as np

import params as P


def _indices_from_stack(stack=P.STACK) -> np.ndarray:
    table = {"H": P.N_HIGH, "L": P.N_LOW}
    return np.array([table[s] for s in stack], dtype=float)


N_LAYERS_IDX = _indices_from_stack()


def _as_2d(d):
    d = np.asarray(d, dtype=float)
    if d.ndim == 1:
        d = d.reshape(1, -1)
    return d.reshape(-1, P.N_LAYERS)


def _phase(d, n_layer, wavelengths):
    wl = np.asarray(wavelengths, dtype=float).ravel()
    return 2.0 * np.pi * d[:, :, None] * n_layer[None, :, None] / wl[None, None, :]


def _characteristic_matrices(delta, n_layer):
    cos_d, sin_d = np.cos(delta), np.sin(delta)
    eta = np.broadcast_to(n_layer[None, :, None], delta.shape)
    M = np.empty(delta.shape + (2, 2), dtype=complex)
    M[..., 0, 0] = cos_d
    M[..., 0, 1] = 1j * sin_d / eta
    M[..., 1, 0] = 1j * eta * sin_d
    M[..., 1, 1] = cos_d
    return M


def _bc(d, wavelengths, n_layer, n_inc, n_sub):
    D = _as_2d(d)
    delta = _phase(D, n_layer, wavelengths)
    M = _characteristic_matrices(delta, n_layer)
    Mtot = M[:, 0]
    for j in range(1, P.N_LAYERS):
        Mtot = Mtot @ M[:, j]
    B = Mtot[..., 0, 0] + Mtot[..., 0, 1] * n_sub
    C = Mtot[..., 1, 0] + Mtot[..., 1, 1] * n_sub
    return B, C


def reflectance_char_matrix(d, wavelengths=P.WAVELENGTHS, n_layer=None,
                            n_inc=None, n_sub=None):
    """主实现：特征矩阵连乘后取 [B; C] = M @ [1; eta_s]，R 由等效导纳 Y = C/B 得到。"""
    n_layer = N_LAYERS_IDX if n_layer is None else np.asarray(n_layer, dtype=float)
    n_inc = P.N_INCIDENT if n_inc is None else float(n_inc)
    n_sub = P.N_SUBSTRATE if n_sub is None else float(n_sub)
    B, C = _bc(d, wavelengths, n_layer, n_inc, n_sub)
    Y = C / B
    r = (n_inc - Y) / (n_inc + Y)
    return np.abs(r) ** 2


def transmittance_char_matrix(d, wavelengths=P.WAVELENGTHS, n_layer=None,
                              n_inc=None, n_sub=None):
    """透射率 T = 4 n0 ns / |n0 B + C|^2，用于无吸收体系的能量守恒检查。"""
    n_layer = N_LAYERS_IDX if n_layer is None else np.asarray(n_layer, dtype=float)
    n_inc = P.N_INCIDENT if n_inc is None else float(n_inc)
    n_sub = P.N_SUBSTRATE if n_sub is None else float(n_sub)
    B, C = _bc(d, wavelengths, n_layer, n_inc, n_sub)
    return 4.0 * n_inc * n_sub / np.abs(n_inc * B + C) ** 2


def reflectance_impedance(d, wavelengths=P.WAVELENGTHS, n_layer=None,
                          n_inc=None, n_sub=None):
    """校验实现：从基底向上做等效导纳递推。

    Y_in = (Y cos d + i eta sin d) / (cos d + i (Y / eta) sin d)
    """
    n_layer = N_LAYERS_IDX if n_layer is None else np.asarray(n_layer, dtype=float)
    n_inc = P.N_INCIDENT if n_inc is None else float(n_inc)
    n_sub = P.N_SUBSTRATE if n_sub is None else float(n_sub)

    D = _as_2d(d)
    delta = _phase(D, n_layer, wavelengths)

    Y = np.full((delta.shape[0], delta.shape[2]), complex(n_sub))
    for j in range(P.N_LAYERS - 1, -1, -1):
        dj = delta[:, j, :]
        ej = n_layer[j]
        c, s = np.cos(dj), np.sin(dj)
        Y = (Y * c + 1j * ej * s) / (c + 1j * (Y / ej) * s)

    r = (n_inc - Y) / (n_inc + Y)
    return np.abs(r) ** 2


# ---------------------------------------------------------------- 解析参照
def reflectance_bare_substrate(n_sub=P.N_SUBSTRATE, n_inc=P.N_INCIDENT):
    """裸基底菲涅耳反射率（无膜层）。"""
    return ((n_inc - n_sub) / (n_inc + n_sub)) ** 2


def reflectance_single_layer(n1, d1, wl, n_inc=P.N_INCIDENT, n_sub=P.N_SUBSTRATE):
    """单层膜解析式（正入射，无吸收）。"""
    r1 = (n_inc - n1) / (n_inc + n1)
    r2 = (n1 - n_sub) / (n1 + n_sub)
    delta = 2.0 * np.pi * n1 * d1 / wl
    c2 = np.cos(2.0 * delta)
    num = r1 ** 2 + r2 ** 2 + 2.0 * r1 * r2 * c2
    den = 1.0 + r1 ** 2 * r2 ** 2 + 2.0 * r1 * r2 * c2
    return num / den


def quarter_wave_thickness(wl, n):
    """四分之一波长光学厚度对应的物理厚度。"""
    return wl / (4.0 * n)


def admittance_chain_qw(wl, n_list, n_sub=P.N_SUBSTRATE):
    """QW 膜系在中心波长的等效导纳链（从基底向上，每层乘 n^2 / Y）。"""
    Y = float(n_sub)
    chain = []
    for n in reversed(list(n_list)):
        Y = float(n) ** 2 / Y
        chain.append(Y)
    return chain
