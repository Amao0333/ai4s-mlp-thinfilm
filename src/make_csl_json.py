# -*- coding: utf-8 -*-
"""把权威元数据转换为 CSL-JSON（citation-style-language 条目格式）。

CSL-JSON 是 Zotero / citeproc 的通用交换格式；论文文献表最终由
tools/render_bibliography.mjs 用 GB/T 7714-2015（Zotero 样式仓库同款样式）渲染。
输出 results/references_csl.json：id 即论文引用顺序 [1]..[12]。
"""
from __future__ import annotations

import json

import params as P

AUTH = P.RES_DIR / "references_authoritative.json"
OUT = P.RES_DIR / "references_csl.json"

# 论文引用顺序（GB/T 7714 顺序编码制：按正文首次引用先后）
ORDER = ["Macleod2018", "Tang2006", "Sullivan1996", "Ma2025iScience", "Peurifoy2018",
         "Liu2018", "Ma2024OptoGPT", "Swe2024", "Malkiel2018", "Harris2020",
         "Paszke2019", "Hestness2017"]

CSL_TYPE = {
    "journal-article": "article-journal",
    "book": "book",
    "conference-paper": "paper-conference",
    # arXiv 预印本：CSL/webpage 在 GB/T 7714-2015 下渲染为 [EB/OL]，
    # 与 arXiv 预印本的性质相符（用 article 会得到不合适的 [A/OL]）
    "preprint": "webpage",
}


def split_name(name: str):
    """中文姓名 -> literal；西文 -> family/given（含 van der 类前缀）。"""
    if all(ord(c) > 127 for c in name.replace(" ", "")):
        return {"literal": name}
    parts = name.split()
    if len(parts) == 1:
        return {"literal": name}
    family = [parts[-1]]
    given = parts[:-1]
    while given and given[-1][:1].islower():
        family.insert(0, given.pop())
    return {"family": " ".join(family), "given": " ".join(given)}


def to_csl(idx: int, v: dict) -> dict:
    item = {
        "id": str(idx),
        "type": CSL_TYPE.get(v.get("type"), "article-journal"),
        "title": v.get("title"),
        "author": [split_name(a) for a in (v.get("authors") or [])],
    }
    if v.get("year"):
        item["issued"] = {"date-parts": [[int(str(v["year"])[:4])]]}
    for src, dst in (("container", "container-title"), ("volume", "volume"),
                     ("issue", "issue"), ("pages", "page"), ("doi", "DOI"),
                     ("publisher", "publisher"), ("place", "publisher-place"),
                     ("edition", "edition"), ("isbn", "ISBN")):
        if v.get(src):
            item[dst] = v[src]
    if v.get("type") == "preprint":
        item["genre"] = "preprint"
        item["URL"] = v.get("url")
        item["container-title"] = "arXiv"
    if v.get("arxiv") and "URL" not in item:
        item["URL"] = f"https://arxiv.org/abs/{v['arxiv']}"
    return item


def main():
    data = json.loads(AUTH.read_text(encoding="utf-8"))
    missing = [k for k in ORDER if k not in data or "error" in data[k]]
    if missing:
        raise SystemExit("权威元数据不完整: " + ", ".join(missing))
    items = [to_csl(i + 1, data[k]) for i, k in enumerate(ORDER)]
    payload = {"items": items, "key_order": ORDER}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written:", OUT)
    for it in items:
        a = it["author"][0]
        first = a.get("literal") or f"{a.get('family')}, {a.get('given')}"
        print(f"  [{it['id']:>2s}] {it['type']:<16s} {first:<22s} {it['title'][:56]}")


if __name__ == "__main__":
    main()
