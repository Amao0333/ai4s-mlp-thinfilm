# -*- coding: utf-8 -*-
"""容量 × 数据量 二维对照：误差的两个自由度，哪个更值得投入？

原稿只做了固定容量下的数据量实验（Q2），和固定数据量下的容量对照（3.4 节）。
两者分开看都会得出片面结论：数据量曲线被容量饱和提前"压平"，容量收益也在特定
数据量下才能兑现。本实验把两个自由度放到同一张网格上，回答一个可操作的问题：
当算力/样本预算有限时，应该优先加数据还是优先加容量？

网格（每个配置单次训练，初始化种子统一为 params.SEED）：
    容量  3 档：small 4–32–32–16–41 / base 4–128–128–64–41 / large 4–256–256–128–41
    数据量 4 档：500 / 1000 / 2000 / 4000（均取自同一训练池的前 N 组）
    验证集与测试集始终不变

已训练过的组合直接复用（base 四个数据量点取自 size_experiment 的同一初始化种子；
small/large 在 4000 组处取自 capacity_experiment），不重复训练。

输出 results/capacity_size_grid.json
"""
from __future__ import annotations

import json

import numpy as np

import params as P
from train import train_idx

CAPS = {"small": (32, 32, 16), "base": P.HIDDEN, "large": (256, 256, 128)}
SIZES = (500, 1000, 2000, 4000)


def n_param_of(hidden):
    sizes = [P.N_LAYERS, *hidden, P.N_WL]
    return sum(sizes[i] * sizes[i + 1] + sizes[i + 1] for i in range(len(sizes) - 1))


def _reuse_path(name, n):
    if name == "base":
        return P.RES_DIR / f"metrics_size{n}_s{P.SEED}.json"
    if n == 4000:
        return P.RES_DIR / f"metrics_cap_{name}.json"
    return None


def main():
    d = np.load(P.DATA_NPZ)
    D, R = d["D"], d["R"]
    idx_train, idx_val, idx_test = d["idx_train"], d["idx_val"], d["idx_test"]

    grid = {}
    for name, hidden in CAPS.items():
        grid[name] = {"hidden": list(hidden), "n_param": n_param_of(hidden), "points": {}}
        for n in SIZES:
            reuse = _reuse_path(name, n)
            if reuse is not None and reuse.exists():
                m = json.loads(reuse.read_text(encoding="utf-8"))
                mse, mae, r2 = m["test"]["mse"], m["test"]["mae"], m["test"]["r2"]
                secs, epochs, reused = m["wall_seconds"], m["epochs_run"], True
            else:
                print(f"[train] cap={name} n_train={n}", flush=True)
                out = train_idx(D, R, idx_train[:n], idx_val, idx_test, P.SEED,
                                tag=f"grid_{name}_{n}", hidden=hidden)
                mse, mae, r2 = out["test"]["mse"], out["test"]["mae"], out["test"]["r2"]
                secs, epochs, reused = out["wall_seconds"], out["epochs_run"], False
            grid[name]["points"][str(n)] = {
                "n_train": int(n), "test_mse": mse, "test_mae": mae, "test_r2": r2,
                "wall_seconds": secs, "epochs_run": epochs, "reused": reused,
            }
            print(f"    -> MSE {mse:.3e}  MAE {mae:.5f}  R2 {r2:.5f}"
                  f"  ({'复用' if reused else f'{secs:.0f}s'})", flush=True)

    # 每个容量的幂律指数（在固定容量下拟合，与 3.2 节口径一致）
    fits = {}
    for name in CAPS:
        pts = grid[name]["points"]
        N = np.array([float(pts[str(n)]["n_train"]) for n in SIZES])
        M = np.array([pts[str(n)]["test_mse"] for n in SIZES])
        slope, intercept = np.polyfit(np.log(N), np.log(M), 1)
        pred = slope * np.log(N) + intercept
        ss_res = float(np.sum((np.log(M) - pred) ** 2))
        ss_tot = float(np.sum((np.log(M) - np.log(M).mean()) ** 2))
        fits[name] = {"alpha": float(-slope), "r2": 1.0 - ss_res / ss_tot}

    # 横向对比：在每个数据量下，"加容量"相对"加数据"的收益
    compare = []
    for n in SIZES:
        row = {"n_train": int(n)}
        for name in CAPS:
            row[f"{name}_mse"] = grid[name]["points"][str(n)]["test_mse"]
        row["large_over_small"] = row["small_mse"] / row["large_mse"]
        row["base_over_small"] = row["small_mse"] / row["base_mse"]
        compare.append(row)

    payload = {
        "caps": {k: list(v) for k, v in CAPS.items()},
        "sizes": list(SIZES),
        "init_seed": P.SEED,
        "note": "除网络结构与训练样本数外，其余设置完全一致；验证集与测试集固定不变",
        "grid": grid,
        "power_law_per_capacity": fits,
        "compare_by_size": compare,
    }
    (P.RES_DIR / "capacity_size_grid.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 74)
    print(f"{'容量':<8}{'参数量':>9} | " + "".join(f"N={n:<12}" for n in SIZES))
    for name in CAPS:
        g = grid[name]
        row = "".join(f"{g['points'][str(n)]['test_mse']:<14.3e}" for n in SIZES)
        print(f"{name:<8}{g['n_param']:>9} | {row}")
    print()
    print("固定容量下的幂律指数：",
          {k: round(v["alpha"], 3) for k, v in fits.items()})
    print("written:", P.RES_DIR / "capacity_size_grid.json")


if __name__ == "__main__":
    main()
