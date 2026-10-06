# -*- coding: utf-8 -*-
"""导出经核验的文献库：references.ris（Zotero 可直接导入）与 references.bib。

全部元数据已通过 Crossref（DOI）、arXiv API、Open Library（ISBN）、
中国高校教材图书网与高校图书馆书目核验，见 results/reference_verification*.json。
"""
from __future__ import annotations

import json

import params as P

REFS = [
    dict(id="Ma2025iScience", type="JOUR", authors=["Ma, Taigao", "Ma, Mingqian", "Guo, L. Jay"],
         title="Optical multilayer thin film structure inverse design: from optimization to deep learning",
         journal="iScience", year=2025, volume="28", pages="112222",
         doi="10.1016/j.isci.2025.112222"),
    dict(id="Macleod2018", type="BOOK", authors=["Macleod, H. Angus"],
         title="Thin-Film Optical Filters", edition="5th", publisher="CRC Press",
         city="Boca Raton", year=2018, isbn="9781138198241"),
    dict(id="Tang2006", type="BOOK", authors=["唐晋发", "顾培夫", "刘旭", "李海峰"],
         title="现代光学薄膜技术", publisher="浙江大学出版社", city="杭州", year=2006,
         isbn="7-308-04977-9", language="zh"),
    dict(id="Peurifoy2018", type="JOUR",
         authors=["Peurifoy, John", "Shen, Yichen", "Jing, Li", "Yang, Yi", "Cano-Renteria, Fidel",
                  "DeLacy, Brendan G.", "Joannopoulos, John D.", "Tegmark, Max", "Soljačić, Marin"],
         title="Nanophotonic particle simulation and inverse design using artificial neural networks",
         journal="Science Advances", year=2018, volume="4", pages="eaar4206",
         doi="10.1126/sciadv.aar4206"),
    dict(id="Liu2018", type="JOUR", authors=["Liu, Dianjing", "Tan, Yixuan", "Khoram, Emad", "Yu, Zongfu"],
         title="Training deep neural networks for the inverse design of nanophotonic structures",
         journal="ACS Photonics", year=2018, volume="5", pages="1365-1369",
         doi="10.1021/acsphotonics.7b01377"),
    dict(id="Malkiel2018", type="JOUR",
         authors=["Malkiel, Itzik", "Mrejen, Michael", "Nagler, Achiya", "Arieli, Uri",
                  "Wolf, Lior", "Suchowski, Haim"],
         title="Plasmonic nanostructure design and characterization via deep learning",
         journal="Light: Science & Applications", year=2018, volume="7", pages="60",
         doi="10.1038/s41377-018-0060-7"),
    dict(id="Ma2024OptoGPT", type="JOUR", authors=["Ma, Taigao", "Wang, Haozhu", "Guo, L. Jay"],
         title="OptoGPT: a foundation model for inverse design in optical multilayer thin film structures",
         journal="Opto-Electronic Advances", year=2024, volume="7", pages="240062",
         doi="10.29026/oea.2024.240062"),
    dict(id="Meng2024", type="JOUR",
         authors=["Meng, Fansheng", "Ding, Jieru", "Zhao, Yu", "Liu, Hui", "Su, Wei",
                  "Yang, Liu", "Tao, Guangming", "Pryamikov, Andrey", "Wang, Xiaocong",
                  "Mu, Hongwei", "et al."],
         title="Inverse design of reflectionless thin-film multilayers with optical absorption "
               "utilizing tandem neural network",
         journal="Photonics", year=2024, volume="11", pages="964",
         doi="10.3390/photonics11100964"),
    dict(id="Sullivan1996", type="JOUR", authors=["Sullivan, Brian T.", "Dobrowolski, J. A."],
         title="Implementation of a numerical needle method for thin-film design",
         journal="Applied Optics", year=1996, volume="35", pages="5484-5492",
         doi="10.1364/AO.35.005484"),
    dict(id="Hestness2017", type="JOUR", authors=["Hestness, Joel", "Narang, Sharan",
                                                 "Ardalani, Newsha", "Diamos, Gregory", "et al."],
         title="Deep learning scaling is predictable, empirically",
         journal="arXiv preprint", year=2017, pages="arXiv:1712.00409",
         url="https://arxiv.org/abs/1712.00409"),
    dict(id="Harris2020", type="JOUR",
         authors=["Harris, Charles R.", "Millman, K. Jarrod", "van der Walt, Stéfan J.", "et al."],
         title="Array programming with NumPy", journal="Nature", year=2020, volume="585",
         pages="357-362", doi="10.1038/s41586-020-2649-2"),
    dict(id="Paszke2019", type="CONF",
         authors=["Paszke, Adam", "Gross, Sam", "Massa, Francisco", "Lerer, Adam", "et al."],
         title="PyTorch: an imperative style, high-performance deep learning library",
         journal="Advances in Neural Information Processing Systems", year=2019, volume="32",
         pages="8024-8035", url="https://arxiv.org/abs/1912.01703"),
]


def ris(ref):
    lines = [f"TY  - {ref['type']}"]
    for a in ref["authors"]:
        lines.append(f"AU  - {a}")
    lines.append(f"TI  - {ref['title']}")
    if ref.get("journal"):
        lines.append(f"JO  - {ref['journal']}")
    if ref.get("edition"):
        lines.append(f"ET  - {ref['edition']}")
    if ref.get("publisher"):
        lines.append(f"PB  - {ref['publisher']}")
    if ref.get("city"):
        lines.append(f"CY  - {ref['city']}")
    lines.append(f"PY  - {ref['year']}")
    if ref.get("volume"):
        lines.append(f"VL  - {ref['volume']}")
    if ref.get("pages"):
        lines.append(f"SP  - {ref['pages']}")
    if ref.get("doi"):
        lines.append(f"DO  - {ref['doi']}")
    if ref.get("isbn"):
        lines.append(f"SN  - {ref['isbn']}")
    if ref.get("url"):
        lines.append(f"UR  - {ref['url']}")
    if ref.get("language"):
        lines.append(f"LA  - {ref['language']}")
    lines.append(f"ID  - {ref['id']}")
    lines.append("ER  - ")
    return "\n".join(lines)


def bib(ref):
    kind = {"JOUR": "article", "BOOK": "book", "CONF": "inproceedings"}[ref["type"]]
    key = ref["id"]
    au = " and ".join(ref["authors"])
    fields = [f"  author    = {{{au}}}", f"  title     = {{{ref['title']}}}"]
    if ref.get("journal"):
        fields.append(f"  journal   = {{{ref['journal']}}}")
    if ref.get("publisher"):
        fields.append(f"  publisher = {{{ref['publisher']}}}")
    if ref.get("city"):
        fields.append(f"  address   = {{{ref['city']}}}")
    if ref.get("edition"):
        fields.append(f"  edition   = {{{ref['edition']}}}")
    fields += [f"  year      = {{{ref['year']}}}"]
    if ref.get("volume"):
        fields.append(f"  volume    = {{{ref['volume']}}}")
    if ref.get("pages"):
        fields.append(f"  pages     = {{{ref['pages']}}}")
    if ref.get("doi"):
        fields.append(f"  doi       = {{{ref['doi']}}}")
    if ref.get("isbn"):
        fields.append(f"  isbn      = {{{ref['isbn']}}}")
    if ref.get("url"):
        fields.append(f"  url       = {{{ref['url']}}}")
    return f"@{kind}{{{key},\n" + ",\n".join(fields) + "\n}"


ris_text = "\n\n".join(ris(r) for r in REFS) + "\n"
bib_text = "\n\n".join(bib(r) for r in REFS) + "\n"

(P.ROOT / "references.ris").write_text(ris_text, encoding="utf-8-sig")
(P.ROOT / "references.bib").write_text(bib_text, encoding="utf-8")
meta = [{"id": r["id"], "title": r["title"], "year": r["year"],
         "doi": r.get("doi"), "isbn": r.get("isbn"), "url": r.get("url")} for r in REFS]
(P.RES_DIR / "references_verified.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"导出 {len(REFS)} 条：references.ris（Zotero 导入用）、references.bib")
