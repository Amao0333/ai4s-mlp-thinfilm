# -*- coding: utf-8 -*-
"""图 9：网络容量与训练样本量的耦合。

同一张双对数坐标里放三条容量曲线，展示两件事：
  1) 幂律指数 α 不是常数，而是随容量从 0.43 升到 1.39；
  2) 样本少时大容量并无优势（N=500 时与基准相当），样本充足后差距才拉开。
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.ticker import NullFormatter

import params as P
from plotstyle import C_GREEN, C_LABEL, C_MLP, C_ORANGE, C_TMM, save

g = json.loads((P.RES_DIR / "capacity_size_grid.json").read_text(encoding="utf-8"))
fits = g["power_law_per_capacity"]

BOUND = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))["R_bound"]


def _fmt_param(n):
    """参数量按量级写成 2.4×10³ 形式（从结果文件读，不在图里写死）。"""
    import math
    e = int(math.floor(math.log10(n)))
    return f"{n / 10 ** e:.1f}\\times10^{{{e}}}"


STYLE = [
    ("small", "小容量", C_ORANGE, "s"),
    ("base", "基准", C_TMM, "o"),
    ("large", "大容量", C_GREEN, "^"),
]

fig, ax = plt.subplots(figsize=(5.33, 2.35))

for name, label, color, marker in STYLE:
    pts = g["grid"][name]["points"]
    N = np.array([float(pts[str(n)]["n_train"]) for n in g["sizes"]])
    M = np.array([pts[str(n)]["test_mse"] for n in g["sizes"]])
    a = fits[name]["alpha"]
    npar = g["grid"][name]["n_param"]
    ax.plot(N, M, marker + "-", color=color, ms=3.4, lw=1.3,
            label=f"{label} ${_fmt_param(npar)}$  ($\\alpha$ = {a:.2f})")

# α = 1 的参考斜率
xr = np.array([500.0, 4000.0])
y0 = g["grid"]["base"]["points"]["500"]["test_mse"]
ax.plot(xr, y0 * (xr / 500.0) ** -1.0, ls=":", lw=0.9, color="#888888",
        label=r"参考斜率 $\alpha$ = 1")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xticks([500, 1000, 2000, 4000])
ax.set_xticklabels(["500", "1000", "2000", "4000"])
ax.xaxis.set_minor_formatter(NullFormatter())   # 只保留主刻度标签
ax.set_xlabel("训练样本数 $N$")
ax.set_ylabel("测试集 MSE")
ax.grid(alpha=0.25, which="both", lw=0.4)
ax.legend(fontsize=6.2, ncol=2, frameon=False, loc="lower left")
save(fig, "fig9_capacity.png")
print("saved figs/fig9_capacity.png")
print("容量幂律指数：", {k: round(v["alpha"], 3) for k, v in fits.items()})
print("N=500 时 large/base 比值: %.3f" %
      (g["grid"]["large"]["points"]["500"]["test_mse"] /
       g["grid"]["base"]["points"]["500"]["test_mse"]))
print("N=4000 时 base/large 比值: %.3f" %
      (g["grid"]["base"]["points"]["4000"]["test_mse"] /
       g["grid"]["large"]["points"]["4000"]["test_mse"]))
