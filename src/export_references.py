# -*- coding: utf-8 -*-
"""由权威元数据（results/references_authoritative.json）导出 references.bib / references.ris。

本脚本不产生任何新信息：所有字段原样取自 fetch_references.py 抓取的权威记录，
只做格式转换。论文正文与文献表最终由 Zotero 管理，这两个文件是导入/交接载体。
"""
from __future__ import annotations

import json

import params as P

AUTH = P.RES_DIR / "references_authoritative.json"
BIB = P.ROOT / "references.bib"
RIS = P.ROOT / "references.ris"


def load():
    return json.loads(AUTH.read_text(encoding="utf-8"))


def _split_name(name: str):
    """返回 (family, given)。中文姓名原样；西文姓名 family 取末位词，
    并把 van / der / de 这类小写前缀并入 family。"""
    if all(ord(c) > 127 for c in name.replace(" ", "")):
        return name, ""
    parts = name.split()
    if len(parts) == 1:
        return name, ""
    family = [parts[-1]]
    given = parts[:-1]
    while given and given[-1][:1].islower():
        family.insert(0, given.pop())
    return " ".join(family), " ".join(given)


def bib_author(name: str) -> str:
    family, given = _split_name(name)
    return f"{family}, {given}" if given else family


def bib_escape(s: str) -> str:
    return (s or "").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def to_bibtex(k: str, v: dict) -> str:
    t = v.get("type")
    authors = " and ".join(bib_author(a) for a in (v.get("authors") or []))
    fields = [("author", authors), ("title", bib_escape(v["title"]))]
    if t == "journal-article":
        entry = "article"
        fields += [("journal", bib_escape(v.get("container") or "")),
                   ("year", str(v.get("year") or ""))]
        if v.get("volume"):
            fields.append(("volume", str(v["volume"])))
        if v.get("issue"):
            fields.append(("number", str(v["issue"])))
        if v.get("pages"):
            fields.append(("pages", str(v["pages"])))
        if v.get("doi"):
            fields.append(("doi", v["doi"]))
    elif t == "conference-paper":
        entry = "inproceedings"
        fields += [("booktitle", bib_escape(v.get("container") or "")),
                   ("year", str(v.get("year") or ""))]
        if v.get("volume"):
            fields.append(("volume", str(v["volume"])))
        if v.get("pages"):
            fields.append(("pages", str(v["pages"])))
        if v.get("publisher"):
            fields.append(("publisher", bib_escape(v["publisher"])))
        if v.get("url"):
            fields.append(("url", v["url"]))
    elif t == "book":
        entry = "book"
        fields += [("publisher", bib_escape(v.get("publisher") or "")),
                   ("year", str(v.get("year") or ""))]
        if v.get("place"):
            fields.append(("address", bib_escape(v["place"])))
        if v.get("edition"):
            fields.append(("edition", v["edition"]))
        if v.get("isbn"):
            fields.append(("isbn", v["isbn"]))
        if v.get("doi"):
            fields.append(("doi", v["doi"]))
    else:  # preprint
        entry = "misc"
        fields += [("year", str(v.get("year") or "")),
                   ("eprint", str(v.get("arxiv") or "")),
                   ("archivePrefix", "arXiv"),
                   ("primaryClass", "cs.LG"),
                   ("url", v.get("url") or "")]
    body = ",\n".join(f"  {n:<12} = {{{val}}}" for n, val in fields if val not in (None, ""))
    return f"@{entry}{{{k},\n{body}\n}}\n"


RIS_TYPES = {
    "journal-article": "JOUR",
    "conference-paper": "CPAPER",
    "book": "BOOK",
    "preprint": "GEN",
}


def to_ris(v: dict) -> str:
    L = [f"TY  - {RIS_TYPES.get(v.get('type'), 'GEN')}"]
    for a in (v.get("authors") or []):
        fam, giv = _split_name(a)
        L.append(f"AU  - {fam}, {giv}" if giv else f"AU  - {fam}")
    if v.get("title"):
        L.append(f"TI  - {v['title']}")
    if v.get("container"):
        L.append(f"{'T2' if v.get('type') != 'journal-article' else 'JO'}  - {v['container']}")
    for tag, f in (("VL", "volume"), ("IS", "issue"), ("SP", "pages"),
                   ("PY", "year"), ("PB", "publisher"), ("CY", "place"),
                   ("ET", "edition"), ("SN", "isbn"), ("DO", "doi"), ("UR", "url")):
        if v.get(f):
            L.append(f"{tag}  - {v[f]}")
    L.append("ER  - ")
    return "\n".join(L) + "\n"


def main():
    data = load()
    order = ["Ma2025iScience", "Macleod2018", "Tang2006", "Peurifoy2018", "Liu2018",
             "Malkiel2018", "Ma2024OptoGPT", "Swe2024", "Sullivan1996", "Hestness2017",
             "Harris2020", "Paszke2019"]
    missing = [k for k in order if k not in data]
    if missing:
        raise SystemExit("权威元数据缺少条目: " + ", ".join(missing))

    bib = "% 由 src/export_references.py 从 results/references_authoritative.json 生成\n" \
          "% 元数据来源：Crossref REST API / arXiv API / 出版社与图书馆 ISBN 记录\n\n"
    bib += "\n".join(to_bibtex(k, data[k]) for k in order)
    BIB.write_text(bib, encoding="utf-8")

    ris = "\n".join(to_ris(data[k]) for k in order)
    RIS.write_text(ris, encoding="utf-8")

    print(f"written: {BIB} ({len(order)} entries)")
    print(f"written: {RIS}")
    for k in order:
        v = data[k]
        print(f"  {k:<16s} {v.get('year')}  {(v.get('authors') or ['?'])[0]:<22s} {v['title'][:58]}")


if __name__ == "__main__":
    main()
