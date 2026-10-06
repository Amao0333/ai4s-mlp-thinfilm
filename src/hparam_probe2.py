# -*- coding: utf-8 -*-
"""长程训练预算探测。（超参数选择时期的探索脚本，不产出结果文件、不属于论文复现链，保留以备追溯）"""
from __future__ import annotations

import time

import numpy as np
import torch
import torch.nn as nn

import params as P
from model import MLP, scale_d

d = np.load(P.DATA_NPZ)
D, R = d["D"], d["R"]
idx = d["idx_train"][:P.N_TRAIN]
idx_va = d["idx_val"]
Xtr = torch.tensor(scale_d(D[idx]), dtype=torch.float32)
Ytr = torch.tensor(R[idx], dtype=torch.float32)
Xva = torch.tensor(scale_d(D[idx_va]), dtype=torch.float32)
Yva = torch.tensor(R[idx_va], dtype=torch.float32)


def run(lr, bs, epochs, seed=P.SEED):
    torch.manual_seed(seed)
    model = MLP(P.HIDDEN)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = nn.MSELoss()
    gen = torch.Generator().manual_seed(seed)
    n = int(Xtr.shape[0])
    t0 = time.perf_counter()
    best = float("inf")
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=gen)
        for i in range(0, n, bs):
            b = perm[i:i + bs]
            opt.zero_grad()
            loss = lossf(model(Xtr[b]), Ytr[b])
            loss.backward()
            opt.step()
        if (ep + 1) % 100 == 0:
            model.eval()
            with torch.no_grad():
                vl = float(lossf(model(Xva), Yva))
            best = min(best, vl)
    return best, time.perf_counter() - t0


for lr, bs, ep in [(3e-3, 512, 2000), (3e-3, 256, 2000)]:
    vl, dt = run(lr, bs, ep)
    print(f"lr={lr:<6g} bs={bs:<4d} epochs={ep:<4d} best_val={vl:.4e}  {dt:6.1f}s")
