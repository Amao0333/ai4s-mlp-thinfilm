# -*- coding: utf-8 -*-
"""公式交付：原生 Word 公式（OMML）。

- 一般公式：写占位段落后调用 officecli 的公式解析器生成 OMML
- 2x2 特征矩阵：officecli 的解析器不支持矩阵换行，改为手工构造 OMML

参考 officecli 的 academic-paper 技能（第 198 行起「Equations」一节）。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from docx.oxml import parse_xml
from docx.oxml.ns import qn

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# 交给 officecli 解析的公式（LaTeX 写法按其解析器支持范围书写）
LATEX = {
    "delta": r"\delta_i = 2\pi n_i d_i / \lambda",
    "bcr": r"[B;\ C] = M\,[1;\ \eta_s],\quad Y = C/B,\quad "
           r"r = \frac{\eta_0 - Y}{\eta_0 + Y},\quad R = |r|^2",
    "adm": r"Y \leftarrow \frac{Y\cos\delta + \mathrm{i}\,\eta\sin\delta}"
           r"{\cos\delta + \mathrm{i}\,(Y/\eta)\sin\delta}",
}


def _run(text, upright=False):
    pr = "<m:rPr><m:nor/></m:rPr>" if upright else ""
    return f'<m:r>{pr}<m:t xml:space="preserve">{text}</m:t></m:r>'


def _plain(text):
    """正体（如虚数单位 i）。"""
    return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t xml:space="preserve">{text}</m:t></m:r>'


def _ssub(base, sub):
    return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"


def matrix_paragraph_xml():
    """2x2 特征矩阵的 OMML。"""
    d_i = _ssub(_run("δ"), _plain("i"))
    eta_i = _ssub(_run("η"), _plain("i"))
    row1 = (f"<m:mr>"
            f"<m:e>{_run('cos', True)}{d_i}</m:e>"
            f"<m:e>{_plain('i')}{_run('sin', True)}{d_i}{_run('/')}{eta_i}</m:e>"
            f"</m:mr>")
    row2 = (f"<m:mr>"
            f"<m:e>{_plain('i')}{eta_i}{_run('sin', True)}{d_i}</m:e>"
            f"<m:e>{_run('cos', True)}{d_i}</m:e>"
            f"</m:mr>")
    mat = f"<m:m><m:mPr/>{row1}{row2}</m:m>"
    math = (f"<m:oMath>{_ssub(_run('M'), _plain('i'))}{_run(' = ')}"
            f"<m:d><m:dPr/><m:e>{mat}</m:e></m:d></m:oMath>")
    return f'<w:p xmlns:w="{W_NS}" xmlns:m="{M_NS}"><m:oMathPara>{math}</m:oMathPara></w:p>'


def insert_matrix(doc):
    """把矩阵公式直接写成一个居中段落。"""
    p = doc.add_paragraph()
    p._p.addnext(parse_xml(matrix_paragraph_xml()))
    p._p.getparent().remove(p._p)


def body_paragraph_index(doc, par):
    """段落在其所属 body 下 w:p 序列中的 1-based 序号（与 officecli 的 p[N] 一致）。"""
    return doc.element.body.findall(qn("w:p")).index(par._p) + 1


def materialize(docx_path: Path, slots):
    """用 officecli 把占位段落替换为原生公式。

    slots: [(占位段落的 paraId, 公式名)]。用 paraId 定位而非位置索引——
    位置索引在插入后会发生偏移，paraId 不受影响。
    """
    for para_id, name in slots:
        latex = LATEX[name]
        path = f"/body/p[@paraId={para_id}]"
        r = subprocess.run(
            ["officecli", "add", str(docx_path), "/body", "--type", "equation",
             "--prop", "mode=display", "--prop", f"formula={latex}", "--before", path],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"officecli add 失败: {r.stdout} {r.stderr}")
        r = subprocess.run(
            ["officecli", "remove", str(docx_path), path],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"officecli remove 失败: {r.stdout} {r.stderr}")
    subprocess.run(["officecli", "close", str(docx_path)], capture_output=True, text=True)
