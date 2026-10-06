# -*- coding: utf-8 -*-
"""随机基线对照：MLP 筛选相对"不看模型、随机挑"的增益。

Q3 问"MLP 能否帮助快速筛选"。要回答得有说服力，必须给出对照基线：
在同一个 10000 组候选池里，若完全不使用代理模型、随机取同样数量的候选，
其目标波长反射率会是多少？MLP 排序把这一水平抬升了多少？

对照设定（与论文 3.3 节完全一致）：
    候选池      design_seed = 303004 生成的 10000 组
    选片数      10（与 MLP Top10 相同）
    基线        等概率无放回随机抽取 10 组，重复 100000 次，取每组最大值
    模型        两两排序取 MLP 最优 Top10 后，用 TMM 真值复核其最大值

输出 results/random_baseline.json
"""
from __future__ import annotations

import json

import numpy as np

import params as P

N_DRAW = 10
N_REPEAT = 100_000
SEED = P.SEED

z = np.load(P.RES_DIR / "design_screening.npz")
r_true = z["r_true_target"]
order_mlp = z["order_mlp"]
n_pool = r_true.size

top10_idx = order_mlp[:N_DRAW]
mlp_best = float(r_true[top10_idx].max())
mlp_top10_mean = float(r_true[top10_idx].mean())

rng = np.random.default_rng(SEED)
draws = rng.random((N_REPEAT, N_DRAW)) * n_pool
draws = draws.astype(np.int64)
base_max = r_true[draws].max(axis=1)
base_mean_of_top = r_true[draws].mean(axis=1)

beat = float((base_max >= mlp_best).mean())

out = {
    "n_pool": int(n_pool),
    "n_draw": N_DRAW,
    "n_repeat": N_REPEAT,
    "seed": int(SEED),
    "mlp_top10": {
        "best_R_tmm": mlp_best,
        "mean_R_tmm": mlp_top10_mean,
    },
    "random_10": {
        "best_R_tmm_mean": float(base_max.mean()),
        "best_R_tmm_median": float(np.median(base_max)),
        "best_R_tmm_p95": float(np.percentile(base_max, 95)),
        "best_R_tmm_p99": float(np.percentile(base_max, 99)),
        "best_R_tmm_max": float(base_max.max()),
        "mean_R_tmm_mean": float(base_mean_of_top.mean()),
        "prob_beat_mlp_top1": beat,
    },
    "gain": {
        "abs_over_random_mean": mlp_best - float(base_max.mean()),
        "abs_over_random_p99": mlp_best - float(np.percentile(base_max, 99)),
        "ratio_over_random_mean": mlp_best / float(base_max.mean()),
    },
    "note": "基线为等概率无放回随机抽取同样数量的候选；MLP 为代理模型排序后取 Top10 并以 TMM 复核",
}
(P.RES_DIR / "random_baseline.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(out, ensure_ascii=False, indent=2))
print()
print(f"随机抽 10 组的最大 R：均值 {base_max.mean():.4f}，99 分位 {np.percentile(base_max, 99):.4f}")
print(f"MLP Top10 的最大 R：{mlp_best:.4f}")
print(f"随机基线超过 MLP 最优的概率：{beat:.2e}")
print("written:", P.RES_DIR / "random_baseline.json")
