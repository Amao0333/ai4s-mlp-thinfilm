# -*- coding: utf-8 -*-
"""公式交付：原生 Word 公式（OMML）。

全部公式由本模块直接构造 OMML 写入 DOCX，不依赖任何外部命令或第三方工具
（早期版本调用 officecli 生成 OMML，该工具为自动更新的外部程序，会因版本变化而失效）。

公式清单（与论文正文一致）：
    式 1  位相厚度      delta
    式 2  单层特征矩阵  matrix（2x2 矩阵，OMML 手工构造）
    式 3  连乘与反射率  bcr
    式 4  等效导纳递推  adm
"""
from __future__ import annotations

from docx.oxml import parse_xml

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# 公式的 LaTeX 源（仅作文档登记与人工核对用，不参与生成）
LATEX = {
    "delta": r"\delta_i = 2\pi n_i d_i / \lambda",
    "matrix": r"M_i = \begin{pmatrix} \cos\delta_i & \mathrm{i}\sin\delta_i/\eta_i \\ "
              r"\mathrm{i}\eta_i\sin\delta_i & \cos\delta_i \end{pmatrix}",
    "bcr": r"[B;\ C] = M\,[1;\ \eta_s],\quad Y = C/B,\quad "
           r"r = \frac{\eta_0 - Y}{\eta_0 + Y},\quad R = |r|^2",
    "adm": r"Y \leftarrow \frac{Y\cos\delta + \mathrm{i}\,\eta\sin\delta}"
           r"{\cos\delta + \mathrm{i}\,(Y/\eta)\sin\delta}",
}


# ----------------------------------------------------------------- OMML 构件
def _run(text):
    """斜体变量。"""
    return f'<m:r><m:t xml:space="preserve">{text}</m:t></m:r>'


def _plain(text):
    """正体（函数名、数字、虚数单位 i 等）。"""
    return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t xml:space="preserve">{text}</m:t></m:r>'


def _ssub(base, sub):
    return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"


def _ssup(base, sup):
    return f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"


def _frac(num, den):
    return f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>"


def _delim(content, beg="(", end=")"):
    return (f'<m:d><m:dPr><m:begChr m:val="{beg}"/><m:endChr m:val="{end}"/>'
            f"</m:dPr><m:e>{content}</m:e></m:d>")


def _para(math):
    """独立显示的公式段落：m:oMathPara 的子元素必须是 m:oMath。"""
    return (f'<w:p xmlns:w="{W_NS}" xmlns:m="{M_NS}">'
            f"<m:oMathPara><m:oMath>{math}</m:oMath></m:oMathPara></w:p>")


# ----------------------------------------------------------------- 各公式
def _eq_delta():
    return _para(
        _ssub(_run("δ"), _plain("i")) + _run(" = 2π")
        + _ssub(_run("n"), _plain("i")) + _ssub(_run("d"), _plain("i"))
        + _run("/") + _run("λ")
    )


def _eq_matrix():
    d_i = _ssub(_run("δ"), _plain("i"))
    eta_i = _ssub(_run("η"), _plain("i"))
    cos_d = _plain("cos ") + d_i
    sin_d = _plain("sin ") + d_i
    row1 = (f"<m:mr>"
            f"<m:e>{cos_d}</m:e>"
            f"<m:e>{_plain('i ')}{sin_d}{_plain('/')}{eta_i}</m:e>"
            f"</m:mr>")
    row2 = (f"<m:mr>"
            f"<m:e>{_plain('i ')}{eta_i}{_plain(' ')}{sin_d}</m:e>"
            f"<m:e>{cos_d}</m:e>"
            f"</m:mr>")
    mat = f"<m:m><m:mPr/>{row1}{row2}</m:m>"
    math = (f"<m:oMath>{_ssub(_run('M'), _plain('i'))}{_plain(' = ')}"
            f"<m:d><m:dPr/><m:e>{mat}</m:e></m:d></m:oMath>")
    return f'<w:p xmlns:w="{W_NS}" xmlns:m="{M_NS}"><m:oMathPara>{math}</m:oMathPara></w:p>'


def _eq_bcr():
    eta_0 = _ssub(_run("η"), _plain("0"))
    eta_s = _ssub(_run("η"), _plain("s"))
    frac = _frac(eta_0 + _plain(" − ") + _run("Y"), eta_0 + _plain(" + ") + _run("Y"))
    r_abs2 = _ssup(_delim(_run("r"), "|", "|"), _plain("2"))
    return _para(
        _plain("[B; C] = ") + _run("M") + _plain(" [1; ") + eta_s + _plain("]")
        + _plain(",   ") + _run("Y") + _plain(" = ") + _run("C") + _plain("/") + _run("B")
        + _plain(",   ") + _run("r") + _plain(" = ") + frac
        + _plain(",   ") + _run("R") + _plain(" = ") + r_abs2
    )


def _eq_adm():
    delta = _run("δ")
    eta = _run("η")
    num = (_run("Y") + _plain(" cos ") + delta + _plain(" + i ")
           + eta + _plain(" sin ") + delta)
    den = (_plain("cos ") + delta + _plain(" + i ")
           + _delim(_run("Y") + _plain("/") + eta) + _plain(" sin ") + delta)
    return _para(_run("Y") + _plain(" ← ") + _frac(num, den))


BUILDERS = {
    "delta": _eq_delta,
    "matrix": _eq_matrix,
    "bcr": _eq_bcr,
    "adm": _eq_adm,
}


def equation_paragraph_xml(name: str) -> str:
    if name not in BUILDERS:
        raise KeyError(f"未知公式: {name}（可选 {sorted(BUILDERS)}）")
    return BUILDERS[name]()


def insert_equation(doc, name: str):
    """在文档末尾插入一个居中的原生公式段落。"""
    anchor = doc.add_paragraph()
    anchor._p.addnext(parse_xml(equation_paragraph_xml(name)))
    anchor._p.getparent().remove(anchor._p)


# 兼容旧调用名
def insert_matrix(doc):
    insert_equation(doc, "matrix")
