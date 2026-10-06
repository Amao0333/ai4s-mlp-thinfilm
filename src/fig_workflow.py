# -*- coding: utf-8 -*-
"""图 1：AI4S 薄膜研究总体流程（四面板）。

字号在保存时统一放大 1.35 倍，故此处文字按短句组织，保证缩放后仍可读。
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

import params as P
from plotstyle import arrow, panel_frame, panel_label, rbox, save

# 物理上限从结果文件读，不在图里写死
R_BOUND = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))["R_bound"]

fig, ax = plt.subplots(figsize=(5.33, 2.52))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ---------------- (a) 数据生成 ----------------
panel_frame(ax, 0.012, 0.600, 0.600, 0.985)
panel_label(ax, 0.028, 0.972, "a")
ax.text(0.310, 0.930, "正向计算与数据生成", ha="center", va="center", fontsize=7.6)
rbox(ax, 0.035, 0.655, 0.165, 0.190, "统一光学模型\n4 层介质膜", "input", fs=7.0)
rbox(ax, 0.225, 0.655, 0.165, 0.190, "TMM 生成数据\n5000 组", "input", fs=7.0)
rbox(ax, 0.415, 0.655, 0.165, 0.190, "固定划分\n4000/500/500", "input", fs=7.0)
arrow(ax, (0.200, 0.750), (0.222, 0.750))
arrow(ax, (0.390, 0.750), (0.412, 0.750))

# ---------------- (b) 代理模型 ----------------
panel_frame(ax, 0.615, 0.600, 0.988, 0.985)
panel_label(ax, 0.631, 0.972, "b")
ax.text(0.800, 0.930, "代理模型训练", ha="center", va="center", fontsize=7.6)
rbox(ax, 0.640, 0.655, 0.325, 0.190, "MLP 代理模型\n4–128–128–64–41", "model", fs=7.2)

# ---------------- (c) 辅助设计 ----------------
panel_frame(ax, 0.012, 0.285, 0.600, 0.575)
panel_label(ax, 0.028, 0.562, "c")
ax.text(0.310, 0.520, "目标波长辅助设计", ha="center", va="center", fontsize=7.6)
rbox(ax, 0.035, 0.330, 0.260, 0.150, "10000 组候选\nMLP 排序 Top10", "output", fs=7.0)
rbox(ax, 0.320, 0.330, 0.260, 0.150, "TMM 复核\n最终 Top5", "output", fs=7.0)
arrow(ax, (0.295, 0.405), (0.318, 0.405))

# ---------------- (d) 校验与参照 ----------------
panel_frame(ax, 0.615, 0.285, 0.988, 0.575)
panel_label(ax, 0.631, 0.562, "d")
ax.text(0.800, 0.520, "校验与性能参照", ha="center", va="center", fontsize=7.6)
rbox(ax, 0.640, 0.382, 0.325, 0.098, "TMM 三级校核", "neutral", fs=7.0)
rbox(ax, 0.640, 0.305, 0.325, 0.062, f"物理上限 {R_BOUND:.4f}", "hl", fs=7.0)

# ---------------- 面板间连线 ----------------
arrow(ax, (0.600, 0.750), (0.613, 0.750))
arrow(ax, (0.800, 0.600), (0.800, 0.578))
arrow(ax, (0.615, 0.405), (0.602, 0.405))

ax.text(0.5, 0.175, "Q1 预测精度    Q2 数据量效应    Q3 辅助设计",
        ha="center", va="center", fontsize=7.0)
ax.text(0.5, 0.080, f"λtarget = {int(P.LAMBDA_TARGET)} nm    seed = {P.SEED}    "
                    f"design_seed = {P.DESIGN_SEED}",
        ha="center", va="center", fontsize=7.0, color="#333333")
ax.text(0.5, 0.020, "全部结果由仓库代码复现", ha="center", va="center",
        fontsize=6.4, color="#808080")

save(fig, "fig1_workflow.png")
