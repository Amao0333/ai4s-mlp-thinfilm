# -*- coding: utf-8 -*-
"""把 paper/manuscript.md 渲染进课程模板，生成 DOCX，并用 Word 导出 PDF。

用法：py src/build_docx.py [模板路径]
默认模板：../AI4S_Research_Template.docx（相对本仓库根目录）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

import params as P

DOCX_OUT = P.ROOT / "paper" / "AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.docx"
PDF_OUT = DOCX_OUT.with_suffix(".pdf")
CENTER = WD_ALIGN_PARAGRAPH.CENTER
FIGURE_WIDTH_CM = 9.3


def find_paragraph(doc, prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    return None


def cut_body_after(doc, anchor):
    body = doc.element.body
    el = anchor._element
    started = False
    for child in list(body):
        if child is el:
            started = True
            continue
        if not started or child.tag.endswith("}sectPr"):
            continue
        body.remove(child)


def set_text(par, text, bold=False):
    for r in list(par.runs):
        r._element.getparent().remove(r._element)
    run = par.add_run(text)
    run.bold = bold
    return par


def body_paragraph(doc, text, indent=True, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    if indent:
        pf.first_line_indent = Pt(2 * size)
    pf.space_after = Pt(2)
    p.add_run(text).font.size = Pt(size)
    return p


def caption_paragraph(doc, text, size=8.5, keep=False):
    """图题/表题：居中，'**图 N**' 加粗。"""
    p = doc.add_paragraph()
    p.alignment = CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    if keep:
        p.paragraph_format.keep_with_next = True
    m = re.match(r"^(\*\*[^*]+\*\*)(.*)$", text)
    head, tail = (m.group(1).strip("*"), m.group(2)) if m else ("", text)
    r1 = p.add_run(head)
    r1.bold = True
    r2 = p.add_run(tail)
    for r in (r1, r2):
        r.font.size = Pt(size)
    return p


def figure_block(doc, name):
    """图片占位段落；图题随后由 caption_run 追加，保证图文不分离。"""
    p = doc.add_paragraph()
    p.alignment = CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_together = True
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(P.FIG_DIR / name), width=Cm(FIGURE_WIDTH_CM))
    return p


def add_caption_into(par, text, size=8.5):
    """把图题追加到图片所在段落（图片下方另起一行）。"""
    par.paragraph_format.keep_with_next = False
    run = par.add_run()
    run.add_break()
    m = re.match(r"^(\*\*[^*]+\*\*)(.*)$", text)
    head, tail = (m.group(1).strip("*"), m.group(2)) if m else ("", text)
    r1 = par.add_run(head)
    r1.bold = True
    r2 = par.add_run(tail)
    for r in (r1, r2):
        r.font.size = Pt(size)
    return par


def add_table_caption(doc, text, size=8.5):
    return caption_paragraph(doc, text, size=size, keep=True)


def add_top5_table(doc):
    ds = json.loads((P.RES_DIR / "design_screening.json").read_text(encoding="utf-8"))
    rows = ds["final_top5"]
    t = doc.add_table(rows=1 + len(rows), cols=7)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    head = ["排名", "d₁ / nm", "d₂ / nm", "d₃ / nm", "d₄ / nm",
            "MLP 预测 R(480 nm)", "TMM 复核 R(480 nm)"]
    for j, h in enumerate(head):
        cell = t.cell(0, j)
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(8)
        cell.paragraphs[0].alignment = CENTER
    for i, row in enumerate(rows, start=1):
        vals = [str(row["final_rank"])] + [f"{x:.2f}" for x in row["d_nm"]] + \
               [f"{row['R_mlp_target']:.4f}", f"{row['R_tmm_target']:.4f}"]
        for j, v in enumerate(vals):
            cell = t.cell(i, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(v)
            run.font.size = Pt(8)
            cell.paragraphs[0].alignment = CENTER
    return t


def render_markdown(doc, md_text):
    lines = md_text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("## 摘要"))
    buf: list[str] = []
    in_refs = False
    pending_fig = None

    def flush():
        if buf:
            body_paragraph(doc, "".join(x.strip() for x in buf))
            buf.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("## 摘要") or s.startswith("# "):
            flush()
            i += 1
            continue
        if s.startswith("{FIG:") or s.startswith("{{FIG:"):
            flush()
            pending_fig = s.split(":")[1].rstrip("}")
            i += 1
            continue
        if s.startswith("{{TABLE:top5}}"):
            flush()
            add_top5_table(doc)
            i += 1
            continue
        if s.startswith("**图") and pending_fig:
            flush()
            par = figure_block(doc, pending_fig)
            add_caption_into(par, s)
            pending_fig = None
            i += 1
            continue
        if s.startswith("**表"):
            flush()
            add_table_caption(doc, s)
            i += 1
            continue
        if s.startswith("### "):
            flush()
            doc.add_heading(s[4:], level=2)
            i += 1
            continue
        if s.startswith("## "):
            flush()
            title = s[3:]
            in_refs = title.startswith("参考文献")
            doc.add_heading(title, level=1)
            i += 1
            continue
        if s.startswith("**关键词**"):
            flush()
            body_paragraph(doc, s.replace("**", ""), indent=False)
            i += 1
            continue
        if in_refs and re.match(r"^\[\d+\]", s):
            flush()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.first_line_indent = Pt(-18)
            p.paragraph_format.space_after = Pt(0.5)
            p.add_run(s).font.size = Pt(8.5)
            i += 1
            continue
        if line.startswith("    ") or s.startswith("https://"):
            flush()
            body_paragraph(doc, s, indent=False, size=9, align=CENTER)
            i += 1
            continue
        buf.append(s)
        i += 1
    flush()


def main():
    template = Path(sys.argv[1]) if len(sys.argv) > 1 else P.ROOT.parent / "AI4S_Research_Template.docx"
    if not template.exists():
        raise SystemExit(f"模板不存在：{template}")
    md_path = P.ROOT / "paper" / "manuscript.md"
    if not md_path.exists():
        raise SystemExit("请先运行 build_values.py 生成 manuscript.md")

    doc = Document(str(template))
    pl = find_paragraph(doc, "姓名：")
    set_text(pl, "姓名：__________    学号：2023303003")
    pt = find_paragraph(doc, "λtarget")
    set_text(pt, f"λtarget：{int(P.LAMBDA_TARGET)} nm    seed：{P.SEED}    "
                 f"design_seed：{P.DESIGN_SEED}")
    anchor = find_paragraph(doc, "Abstract")
    set_text(anchor, "摘要")
    cut_body_after(doc, anchor)

    render_markdown(doc, md_path.read_text(encoding="utf-8"))
    DOCX_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(DOCX_OUT))
    print("DOCX:", DOCX_OUT)

    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        d = word.Documents.Open(str(DOCX_OUT))
        d.SaveAs(str(PDF_OUT), FileFormat=17)
        pages = d.ComputeStatistics(2)
        d.Close(False)
        word.Quit()
        print("PDF:", PDF_OUT, "| 页数:", pages)
    except Exception as e:
        print("PDF 导出失败（DOCX 已生成）:", e)


if __name__ == "__main__":
    main()
