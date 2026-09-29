# -*- coding: utf-8 -*-
"""图 1：AI4S 薄膜研究总体流程（四面板）。"""
from __future__ import annotations

import matplotlib.pyplot as plt

import params as P
from plotstyle import arrow, panel_frame, panel_label, rbox, save

fig, ax = plt.subplots(figsize=(7.2, 3.5))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ---------------- (a) 正向计算与数据生成 ----------------
panel_frame(ax, 0.012, 0.615, 0.575, 0.985)
panel_label(ax, 0.028, 0.972, "a")
ax.text(0.30, 0.945, "正向计算与数据生成", ha="center", va="center", fontsize=8.2)

rbox(ax, 0.030, 0.660, 0.155, 0.215,
     "统一光学模型\nAir/H/L/H/L/Glass\n$n_H$=2.30  $n_L$=1.45\n$n_s$=1.52", "input", fs=7.4)
rbox(ax, 0.212, 0.660, 0.155, 0.215,
     "TMM 计算\n5000 组膜厚\n40–180 nm\n41 点光谱", "input", fs=7.4)
rbox(ax, 0.394, 0.660, 0.155, 0.215,
     "固定划分\n4000 训练\n500 验证\n500 测试", "input", fs=7.4)
for x0 in (0.185, 0.367):
    arrow(ax, (x0, 0.767), (x0 + 0.027, 0.767))

# ---------------- (b) 代理模型 ----------------
panel_frame(ax, 0.592, 0.615, 0.988, 0.985)
panel_label(ax, 0.608, 0.972, "b")
ax.text(0.79, 0.945, "代理模型训练", ha="center", va="center", fontsize=8.2)

rbox(ax, 0.615, 0.660, 0.350, 0.215,
     "MLP 代理模型\n4–128–128–64–41\nReLU，MSE 损失\nAdam，早停", "model", fs=7.6)

# ---------------- (c) 辅助设计 ----------------
panel_frame(ax, 0.012, 0.315, 0.575, 0.585)
panel_label(ax, 0.028, 0.572, "c")
ax.text(0.30, 0.552, "目标波长辅助设计", ha="center", va="center", fontsize=8.2)

rbox(ax, 0.030, 0.360, 0.245, 0.160,
     "生成 10000 组候选\n（design_seed）\nMLP 预测并排序", "output", fs=7.4)
rbox(ax, 0.305, 0.360, 0.245, 0.160,
     "TMM 复核 Top10\n真值重排\n确定最终 Top5", "output", fs=7.4)
arrow(ax, (0.278, 0.440), (0.302, 0.440))

# ---------------- (d) 校验与参照 ----------------
panel_frame(ax, 0.592, 0.315, 0.988, 0.585)
panel_label(ax, 0.608, 0.572, "d")
ax.text(0.79, 0.552, "校验与性能参照", ha="center", va="center", fontsize=8.2)

rbox(ax, 0.615, 0.412, 0.350, 0.088,
     "TMM 三级校核：解析解 / 双实现 / 在线 TMM", "neutral", fs=7.2)
rbox(ax, 0.615, 0.322, 0.350, 0.088,
     "物理上限：QW 解析解 + 全局优化", "hl", fs=7.2)

# ---------------- 面板间连线 ----------------
arrow(ax, (0.575, 0.800), (0.590, 0.800))
arrow(ax, (0.790, 0.615), (0.790, 0.588))
arrow(ax, (0.592, 0.450), (0.577, 0.450))

ax.text(0.5, 0.185, "Q1  MLP 能否准确预测反射光谱？        "
                    "Q2  训练数据量增加后误差如何变化？        "
                    "Q3  MLP 能否辅助目标波长下的薄膜设计？",
        ha="center", va="center", fontsize=7.6)
ax.text(0.5, 0.075, f"个人参数：$\lambda_{{target}}$ = {int(P.LAMBDA_TARGET)} nm    "
                    f"seed = {P.SEED}    design_seed = {P.DESIGN_SEED}",
        ha="center", va="center", fontsize=8.0, color="#333333")
ax.text(0.5, 0.005, "全部结果由仓库代码复现", ha="center", va="bottom",
        fontsize=7.0, color="#808080")

save(fig, "fig1_workflow.png")
