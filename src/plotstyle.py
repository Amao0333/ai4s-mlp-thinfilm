# -*- coding: utf-8 -*-
"""统一绘图风格（中文标注，300 dpi）。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import params as P

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei"],
    "axes.unicode_minus": False,
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.4,
    "legend.frameon": False,
    "figure.facecolor": "white",
})

C_TMM = "#1f4e79"
C_MLP = "#c00000"
C_GREY = "#7f7f7f"
C_GREEN = "#2e7d32"
C_ORANGE = "#e07b00"


def save(fig, name):
    path = P.FIG_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print("saved", path)
    return path


# ---------------------------------------------------------------- 示意图组件
# 配色参考 Opto-Electronic Advances 论文的示意图规范：
# 输入=浅蓝，模型=浅绿，输出=浅橙，中性=浅灰；面板用虚线框 + 蓝底白字标号。
PALETTE = {
    "input":  {"fc": "#dae3f3", "ec": "#8eaadb"},
    "model":  {"fc": "#e2efda", "ec": "#a9d08e"},
    "output": {"fc": "#fbe5d6", "ec": "#f4b183"},
    "neutral": {"fc": "#f2f2f2", "ec": "#bfbfbf"},
    "hl":     {"fc": "#fff2cc", "ec": "#d6b656"},
}
C_PANEL = "#a6a6a6"
C_LABEL = "#1f6fb5"


def rbox(ax, x, y, w, h, text, kind="neutral", fs=8.0, ls=1.45, bold=False,
         rounding=0.02, lw=1.0, zorder=2):
    from matplotlib.patches import FancyBboxPatch
    st = PALETTE[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.008,rounding_size={rounding}",
                                linewidth=lw, facecolor=st["fc"], edgecolor=st["ec"],
                                zorder=zorder))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            linespacing=ls, zorder=zorder + 1, fontweight="bold" if bold else "normal")


def panel_frame(ax, x0, y0, x1, y1):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                boxstyle="round,pad=0.004,rounding_size=0.015",
                                linewidth=0.9, facecolor="none", edgecolor=C_PANEL,
                                linestyle=(0, (4, 3)), zorder=1))


def panel_label(ax, x, y, letter, size=8.5):
    ax.text(x, y, letter, ha="left", va="top", fontsize=size, color="white",
            fontweight="bold", zorder=6,
            bbox=dict(boxstyle="square,pad=0.28", facecolor=C_LABEL, edgecolor="none"))


def arrow(ax, p1, p2, color="#404040", lw=1.0, style="-|>", ms=9, zorder=3, ls="-"):
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms,
                                 linewidth=lw, color=color, linestyle=ls,
                                 shrinkA=0, shrinkB=0, zorder=zorder))


def panel_letter(ax, s, x=-0.14, y=1.02):
    """子图左上角的蓝底白字面板标号。"""
    ax.text(x, y, s, transform=ax.transAxes, ha="left", va="bottom", fontsize=8.5,
            color="white", fontweight="bold", zorder=8,
            bbox=dict(boxstyle="square,pad=0.26", facecolor=C_LABEL, edgecolor="none"))
