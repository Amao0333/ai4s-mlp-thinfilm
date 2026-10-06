# -*- coding: utf-8 -*-
"""模型容量对照实验：误差瓶颈在数据，还是在网络容量？

论文 3.4/4 节承认"误差仍有约 86% 的方差未被所考察特征解释"，但此前只归因于
采样密度，从未检验"网络容量是否本身就是限制"。本实验补上这一检验。

设定：训练数据（4000 组）、验证/测试集、初始化种子、优化器、学习率、批大小、
训练轮数上限与早停耐心全部相同，**只改隐藏层结构**：

    small   4– 32– 32– 16–41      约 2.4×10³ 参数（基准的 1/11）
    base    4–128–128– 64–41      约 2.8×10⁴ 参数（论文基准，直接复用已有结果）
    large   4–256–256–128–41      约 1.1×10⁵ 参数（基准的 3.7 倍）

若三者测试误差相近，说明在给定训练预算下容量已饱和，误差来自数据分布；
若误差随容量单调下降，则容量是限制之一，需修正论文结论。

输出 results/capacity_experiment.json
"""
from __future__ import annotations

import json

import numpy as np

import params as P
from train import train_idx

CONFIGS = {
    "small": (32, 32, 16),
    "large": (256, 256, 128),
}


def main():
    d = np.load(P.DATA_NPZ)
    D, R = d["D"], d["R"]
    idx_train, idx_val, idx_test = d["idx_train"], d["idx_val"], d["idx_test"]

    runs = {}

    # 基准：直接复用已训练好的模型结果，不重复训练
    mb = json.loads((P.RES_DIR / "metrics_base.json").read_text(encoding="utf-8"))
    _bs = [P.N_LAYERS, *P.HIDDEN, P.N_WL]
    _base_param = sum(_bs[i] * _bs[i + 1] + _bs[i + 1] for i in range(len(_bs) - 1))
    runs["base"] = {
        "hidden": list(P.HIDDEN),
        "n_param": _base_param,
        "epochs_run": mb["epochs_run"],
        "best_epoch": mb["best_epoch"],
        "val_mse": mb["val_mse_best"],
        "test": mb["test"],
        "wall_seconds": mb["wall_seconds"],
        "reused": True,
    }

    for name, hidden in CONFIGS.items():
        print(f"\n=== 训练 {name} 容量 {hidden} ===", flush=True)
        out = train_idx(D, R, idx_train, idx_val, idx_test, P.SEED,
                        tag=f"cap_{name}", hidden=hidden)
        runs[name] = {
            "hidden": list(hidden),
            "n_param": out.get("n_param"),
            "epochs_run": out["epochs_run"],
            "best_epoch": out["best_epoch"],
            "val_mse": out["val_mse_best"],
            "test": out["test"],
            "wall_seconds": out["wall_seconds"],
            "reused": False,
        }

    base_mse = runs["base"]["test"]["mse"]
    summary = []
    for name in ("small", "base", "large"):
        r = runs[name]
        summary.append({
            "config": name,
            "n_param": r["n_param"],
            "test_mse": r["test"]["mse"],
            "test_mae": r["test"]["mae"],
            "test_r2": r["test"]["r2"],
            "rel_mse_vs_base": r["test"]["mse"] / base_mse - 1.0,
            "wall_seconds": r["wall_seconds"],
        })

    payload = {
        "n_train": int(idx_train.size),
        "init_seed": P.SEED,
        "note": "除隐藏层结构外，训练数据、划分、种子、超参数与训练预算完全一致",
        "runs": runs,
        "summary": summary,
    }
    (P.RES_DIR / "capacity_experiment.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 62)
    print(f"{'配置':<8}{'参数量':>10}{'测试 MSE':>14}{'相对基准':>12}{'R²':>10}")
    for s in summary:
        print(f"{s['config']:<8}{s['n_param']:>10d}{s['test_mse']:>14.3e}"
              f"{s['rel_mse_vs_base']:>+11.2%}{s['test_r2']:>10.4f}")
    print("written:", P.RES_DIR / "capacity_experiment.json")


if __name__ == "__main__":
    main()
