# -*- coding: utf-8 -*-
"""按 DOI 精确核验（Crossref）+ arXiv API 核验预印本。"""
from __future__ import annotations

import json
import time
import urllib.request

import params as P

UA = "ai4s-thinfilm-reference-check/1.0 (mailto:noreply@example.com)"

DOIS = {
    "iScience2025": "10.1016/j.isci.2025.112222",
    "Peurifoy2018": "10.1126/sciadv.aar4206",
    "Liu2018": "10.1021/acsphotonics.7b01377",
    "Malkiel2018": "10.1038/s41377-018-0060-7",
    "OptoGPT2024": "10.29026/oea.2024.240062",
    "Meng2024": "10.3390/photonics11100964",
    "Sullivan1996": "10.1364/AO.35.005484",
    "NumPy2020": "10.1038/s41586-020-2649-2",
}
ARXIV = {"Hestness2017": "1712.00409", "PyTorch2019": "1912.01703"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def fmt_crossref(js):
    it = js["message"]
    au = it.get("author") or []
    names = [" ".join(x for x in (a.get("family"), a.get("given")) if x) for a in au]
    year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {
        "doi": it.get("DOI"),
        "title": (it.get("title") or [""])[0],
        "journal": (it.get("container-title") or [""])[0],
        "year": year,
        "volume": it.get("volume"),
        "issue": it.get("issue"),
        "pages": it.get("page") or it.get("article-number"),
        "authors_short": (", ".join(names[:3]) + (" et al." if len(names) > 3 else "")),
        "type": it.get("type"),
    }


out = {"crossref": {}, "arxiv": {}}
for key, doi in DOIS.items():
    try:
        js = json.loads(get("https://api.crossref.org/works/" + doi))
        out["crossref"][key] = fmt_crossref(js)
        m = out["crossref"][key]
        print(f"[{key}] {m['doi']} | {m['journal']} {m['year']} | vol {m['volume']} | p {m['pages']}")
    except Exception as e:
        out["crossref"][key] = {"doi": doi, "error": str(e)}
        print(f"[{key}] 失败: {e}")
    time.sleep(0.5)

import re
for key, aid in ARXIV.items():
    try:
        xml = get(f"http://export.arxiv.org/api/query?id_list={aid}")
        title = re.search(r"<title>(.*?)</title>", xml[200:], re.S)
        authors = re.findall(r"<name>(.*?)</name>", xml)
        published = re.search(r"<published>(\d{4})", xml)
        out["arxiv"][key] = {"arxiv": aid, "title": (title.group(1).strip() if title else ""),
                             "authors": authors[:4], "year": published.group(1) if published else None}
        print(f"[{key}] arXiv:{aid} | {out['arxiv'][key]['title'][:60]}... | {out['arxiv'][key]['year']}")
    except Exception as e:
        out["arxiv"][key] = {"arxiv": aid, "error": str(e)}
        print(f"[{key}] 失败: {e}")
    time.sleep(1)

(P.RES_DIR / "reference_verification_doi.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten:", P.RES_DIR / "reference_verification_doi.json")
