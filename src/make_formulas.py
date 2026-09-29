# -*- coding: utf-8 -*-
"""把论文中的公式渲染为矢量级数学排版图片（matplotlib mathtext，400 dpi）。

正文里的 ASCII 公式（如 "δ_i = 2π n_i d_i / λ"）替换为 {{EQ:名称}} 标记，
由 build_docx.py 按原始尺寸插入图片，保证公式以真正的数学排版呈现。
输出 figs/formulas/*.png 与 results/formula_meta.json
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import params as P

matplotlib.rcParams.update({
    "mathtext.fontset": "cm",
    "font.family": "serif",
})

OUT = P.FIG_DIR / "formulas"
OUT.mkdir(parents=True, exist_ok=True)
DPI = 400
FS = 10.0          # 公式字号（pt），插入论文后即为实际字号


def render(name, draw, width, height):
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    draw(ax)
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=DPI, transparent=False, facecolor="white",
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    from PIL import Image
    with Image.open(path) as im:
        w_cm = im.width / DPI * 2.54
        h_cm = im.height / DPI * 2.54
    return {"file": f"{name}.png", "width_cm": round(w_cm, 3), "height_cm": round(h_cm, 3)}


def eq_delta(ax):
    ax.text(0.5, 0.5, r"$\delta_i = 2\pi n_i d_i / \lambda$",
            ha="center", va="center", fontsize=FS)


def eq_bc(ax):
    ax.text(0.5, 0.5, r"$[B;\ C] = M\,[1;\ \eta_s]\,,\qquad Y = C/B$",
            ha="center", va="center", fontsize=FS)


def eq_bcr(ax):
    ax.text(0.5, 0.5,
            r"$[B;\ C] = M\,[1;\ \eta_s]\,,\quad Y = C/B\,,\quad "
            r"r = \dfrac{\eta_0 - Y}{\eta_0 + Y}\,,\quad R = |r|^2$",
            ha="center", va="center", fontsize=FS)


def eq_rR(ax):
    ax.text(0.5, 0.5,
            r"$r = \dfrac{\eta_0 - Y}{\eta_0 + Y}\,,\qquad R = |r|^2$",
            ha="center", va="center", fontsize=FS)


def eq_adm(ax):
    ax.text(0.5, 0.5,
            r"$Y \leftarrow \dfrac{Y\cos\delta + \mathrm{i}\,\eta\sin\delta}"
            r"{\cos\delta + \mathrm{i}\,(Y/\eta)\sin\delta}$",
            ha="center", va="center", fontsize=FS)


def eq_matrix(ax):
    """2x2 特征矩阵。

    括号位置由文字实际渲染范围反推，避免线条压在公式上。
    """
    fig = ax.figure
    rows = [0.70, 0.30]
    cells = [r"$\cos\delta_i$", r"$\mathrm{i}\,\sin\delta_i/\eta_i$",
             r"$\mathrm{i}\,\eta_i\sin\delta_i$", r"$\cos\delta_i$"]
    artists = []
    for r, y in enumerate(rows):
        for c in range(2):
            t = ax.text(0.5 + c * 0.30, y, cells[r * 2 + c],
                        ha="center", va="center", fontsize=FS)
            artists.append(t)
    label = ax.text(0.30, 0.5, r"$M_i =$", ha="center", va="center", fontsize=FS)
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transAxes.inverted()

    def ext(t):
        bb = t.get_window_extent(renderer=rend)
        p0 = inv.transform((bb.x0, bb.y0))
        p1 = inv.transform((bb.x1, bb.y1))
        return p0, p1

    xs0 = [ext(t)[0][0] for t in artists]
    xs1 = [ext(t)[1][0] for t in artists]
    ys0 = [ext(t)[0][1] for t in artists]
    ys1 = [ext(t)[1][1] for t in artists]
    x_left, x_right = min(xs0), max(xs1)
    y_bot, y_top = min(ys0) - 0.10, max(ys1) + 0.10
    for x, sgn in ((x_left - 0.035, 1), (x_right + 0.035, -1)):
        ax.plot([x, x], [y_bot, y_top], color="black", lw=1.1, solid_capstyle="butt")
        ax.plot([x, x + 0.030 * sgn], [y_top, y_top], color="black", lw=1.1)
        ax.plot([x, x + 0.030 * sgn], [y_bot, y_bot], color="black", lw=1.1)
    # 把 M_i = 放到左括号左侧
    lp = ext(label)[1][0]
    label.set_position((x_left - 0.075 - (lp - ext(label)[0][0]) / 2, 0.5))


SPECS = [
    ("delta", eq_delta, 2.0, 0.26),
    ("matrix", eq_matrix, 3.0, 0.56),
    ("bcr", eq_bcr, 4.6, 0.42),
    ("rR", eq_rR, 2.6, 0.42),
    ("adm", eq_adm, 3.0, 0.52),
]

meta = {}
for name, fn, w, h in SPECS:
    meta[name] = render(name, fn, w, h)
    print(name, meta[name])

(P.RES_DIR / "formula_meta.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("written:", P.RES_DIR / "formula_meta.json")
