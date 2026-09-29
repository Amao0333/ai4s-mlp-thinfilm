# -*- coding: utf-8 -*-
"""《薄膜技术》AI4S 大作业 —— 全局参数

所有脚本只从这里取值，保证代码、图表、论文三者口径完全一致。
个人参数由学号派生：lambda_target、seed、design_seed。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- 个人参数
STUDENT_ID = "2023303003"
N_LAST2 = int(STUDENT_ID[-2:])                    # 03
SEED = int(STUDENT_ID[-6:])                       # 303003
DESIGN_SEED = SEED + 1                            # 303004
LAMBDA_TARGET = 450 + 10 * (N_LAST2 % 31)         # 450 + 30 = 480 nm

# ---------------------------------------------------------------- 光学模型
N_INCIDENT = 1.00      # Air
N_HIGH = 2.30          # H
N_LOW = 1.45           # L
N_SUBSTRATE = 1.52     # Glass
STACK = ("H", "L", "H", "L")
N_LAYERS = len(STACK)

WL_MIN, WL_MAX, WL_STEP = 400.0, 800.0, 10.0
WAVELENGTHS = np.arange(WL_MIN, WL_MAX + 0.5 * WL_STEP, WL_STEP)   # 41 点
N_WL = len(WAVELENGTHS)

D_MIN, D_MAX = 40.0, 180.0

# ---------------------------------------------------------------- 数据集
N_TOTAL = 5000
N_TRAIN, N_VAL, N_TEST = 4000, 500, 500
N_DESIGN = 10000

# ---------------------------------------------------------------- 模型与训练
HIDDEN = (128, 128, 64)
N_EPOCHS = 4000
BATCH_SIZE = 256
LR = 3e-3
PATIENCE = 400
TRAIN_SEEDS = (SEED, SEED + 1000, SEED + 2000)    # 重复实验的初始化种子
SIZE_LEVELS = (500, 1000, 2000, 4000)

# ---------------------------------------------------------------- 路径
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figs"
RES_DIR = ROOT / "results"
CFG_DIR = ROOT / "configs"
for _d in (DATA_DIR, FIG_DIR, RES_DIR, CFG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DATA_NPZ = DATA_DIR / "thinfilm_dataset.npz"
DESIGN_NPZ = DATA_DIR / "design_candidates.npz"
BASE_MODEL = RES_DIR / "base_model.pt"


def as_dict() -> dict:
    return {
        "student_id": STUDENT_ID,
        "n_last2": N_LAST2,
        "lambda_target_nm": LAMBDA_TARGET,
        "seed": SEED,
        "design_seed": DESIGN_SEED,
        "target_rule": "lambda_target = 450 + 10 * (N mod 31), seed = last 6 digits, design_seed = seed + 1",
        "optics": {
            "incident": N_INCIDENT, "high": N_HIGH, "low": N_LOW, "substrate": N_SUBSTRATE,
            "stack": list(STACK), "n_layers": N_LAYERS,
            "wavelength_range_nm": [WL_MIN, WL_MAX, WL_STEP], "n_wavelengths": N_WL,
            "thickness_range_nm": [D_MIN, D_MAX],
        },
        "dataset": {"n_total": N_TOTAL, "n_train": N_TRAIN, "n_val": N_VAL, "n_test": N_TEST,
                    "n_design_candidates": N_DESIGN},
        "model": {"layers": [N_LAYERS, *HIDDEN, N_WL], "activation": "ReLU", "loss": "MSE",
                  "optimizer": "Adam", "lr": LR, "batch_size": BATCH_SIZE,
                  "max_epochs": N_EPOCHS, "early_stop_patience": PATIENCE,
                  "input_scaling": "(d - 40) / 140", "output": "linear",
                  "train_seeds": list(TRAIN_SEEDS)},
        "train_size_levels": list(SIZE_LEVELS),
    }


def dump() -> Path:
    p = CFG_DIR / "config.json"
    p.write_text(json.dumps(as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p


if __name__ == "__main__":
    print(json.dumps(as_dict(), ensure_ascii=False, indent=2))
    print("config written:", dump())
