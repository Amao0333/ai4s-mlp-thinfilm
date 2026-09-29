# -*- coding: utf-8 -*-
"""第 5 步：用个人 seed 生成 5000 组膜厚—光谱数据，并固定划分 4000/500/500。

复现约定（与作业说明一致，用 legacy 随机 API 保证跨 numpy 版本流一致）：
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    D = D_MIN + (D_MAX - D_MIN) * np.random.rand(5000, 4)
    perm = np.random.permutation(5000)
    训练池 = perm[:4000]（顺序即 perm 中的顺序，前 N 组即该序列前 N 个）
    验证集 = perm[4000:4500]   测试集 = perm[4500:5000]

输出 data/thinfilm_dataset.npz
"""
from __future__ import annotations

import json
import random

import numpy as np

import params as P
import tmm


def main() -> None:
    random.seed(P.SEED)
    np.random.seed(P.SEED)
    try:
        import torch
        torch.manual_seed(P.SEED)
    except Exception:
        pass

    D = P.D_MIN + (P.D_MAX - P.D_MIN) * np.random.rand(P.N_TOTAL, P.N_LAYERS)
    perm = np.random.permutation(P.N_TOTAL)

    idx_train = perm[:P.N_TRAIN]
    idx_val = perm[P.N_TRAIN:P.N_TRAIN + P.N_VAL]
    idx_test = perm[P.N_TRAIN + P.N_VAL:]

    R = tmm.reflectance_char_matrix(D)

    np.savez_compressed(
        P.DATA_NPZ,
        D=D, R=R, perm=perm,
        idx_train=idx_train, idx_val=idx_val, idx_test=idx_test,
        wavelengths=P.WAVELENGTHS,
        target_index=np.array([int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))]),
    )

    meta = {
        "n_total": P.N_TOTAL, "n_train": int(idx_train.size),
        "n_val": int(idx_val.size), "n_test": int(idx_test.size),
        "seed": P.SEED,
        "D_min_max": [float(D.min()), float(D.max())],
        "R_min_max": [float(R.min()), float(R.max())],
        "R_at_target_train": {
            "min": float(R[idx_train, 8].min()), "max": float(R[idx_train, 8].max()),
            "mean": float(R[idx_train, 8].mean()), "std": float(R[idx_train, 8].std()),
        },
        "split_head_train": idx_train[:10].tolist(),
        "split_head_val": idx_val[:10].tolist(),
        "split_head_test": idx_test[:10].tolist(),
    }
    (P.RES_DIR / "dataset_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print("written:", P.DATA_NPZ)


if __name__ == "__main__":
    main()
