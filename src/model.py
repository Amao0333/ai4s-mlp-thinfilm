# -*- coding: utf-8 -*-
"""MLP 代理模型定义（4 -> 128 -> 128 -> 64 -> 41）。"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

import params as P


def scale_d(d):
    """膜厚归一化到 [0, 1]：(d - 40) / 140。"""
    return (np.asarray(d, dtype=float) - P.D_MIN) / (P.D_MAX - P.D_MIN)


class MLP(nn.Module):
    def __init__(self, hidden=P.HIDDEN, n_in=P.N_LAYERS, n_out=P.N_WL):
        super().__init__()
        layers = []
        prev = n_in
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers.append(nn.Linear(prev, n_out))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)
