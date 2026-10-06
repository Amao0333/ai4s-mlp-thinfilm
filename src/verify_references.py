# -*- coding: utf-8 -*-
"""用 Crossref（DOI 官方注册机构）核验参考文献的真实元数据。

输出 results/reference_verification.json 与 references.bib（可导入 Zotero）。
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

import params as P

API = "https://api.crossref.org/works"
UA = "ai4s-thinfilm-reference-check/1.0 (mailto:noreply@example.com)"

# 待核验条目：论文中使用的题名
CANDIDATES = [
    ("iScience2025", "Optical multilayer thin film structure inverse design: from optimization to deep learning"),
    ("MacleodBook", "Thin-Film Optical Filters"),
    ("Peurifoy2018", "Nanophotonic particle simulation and inverse design using artificial neural networks"),
    ("Liu2018", "Training Deep Neural Networks for the Inverse Design of Nanophotonic Structures"),
    ("Malkiel2018", "Plasmonic nanostructure design and characterization via Deep Learning"),
    ("OptoGPT2024", "OptoGPT: a foundation model for inverse design in optical multilayer thin film structures"),
    ("Meng2024", "Inverse Design of Reflectionless Thin-Film Multilayers with Optical Absorption Utilizing Tandem Neural Network"),
    ("Sullivan1996", "Implementation of a numerical needle method for thin-film design"),
    ("Hestness2017", "Deep learning scaling is predictable, empirically"),
    ("NumPy2020", "Array programming with NumPy"),
    ("PyTorch2019", "PyTorch: An Imperative Style, High-Performance Deep Learning Library"),
]


def query(title):
    url = API + "?" + urllib.parse.urlencode({
        "query.bibliographic": title, "rows": 3, "select":
        "DOI,title,container-title,volume,issue,page,article-number,issued,author,type,publisher"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["items"]


def brief(it):
    au = it.get("author") or []
    names = ", ".join(f"{a.get('family','')} {a.get('given','')}".strip() for a in au[:3])
    year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {
        "doi": it.get("DOI"),
        "title": (it.get("title") or [""])[0],
        "journal": (it.get("container-title") or [""])[0] or it.get("publisher", ""),
        "year": year,
        "volume": it.get("volume"),
        "issue": it.get("issue"),
        "pages": it.get("page") or it.get("article-number"),
        "authors": names + (" et al." if len(au) > 3 else ""),
        "type": it.get("type"),
    }


out = {}
for key, title in CANDIDATES:
    try:
        items = query(title)
        out[key] = {"query_title": title, "matches": [brief(i) for i in items]}
        print(f"[{key}] 命中 {len(items)} 条，首选 DOI: {items[0].get('DOI')}")
    except Exception as e:
        out[key] = {"query_title": title, "error": str(e)}
        print(f"[{key}] 查询失败: {e}")
    time.sleep(0.6)

(P.RES_DIR / "reference_verification.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten:", P.RES_DIR / "reference_verification.json")
