#!/usr/bin/env python3
"""Extract person-like Author pages from a Kiwix text export."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from opencc import OpenCC

RECORD_START = re.compile(r"^\[(\d{6})\]$")
TITLE_LINE = "标题："
URL_LINE = "URL："
INFO_LINE = "信息："
AUTHOR_PREFIX = "Author:"

# Conservative signals for institutional, organizational, document, and topic pages.
NON_PERSON_KEYWORDS = (
    "人民代表大会",
    "委员会",
    "国务院",
    "人民政府",
    "办公厅",
    "法院",
    "检察院",
    "大学",
    "学院",
    "研究院",
    "科学院",
    "出版社",
    "公司",
    "协会",
    "基金会",
    "组织",
    "中央委员会",
    "共产党",
    "民主党",
    "部",
    "局",
    "厅",
    "署",
    "馆",
    "医院",
    "学校",
    "数据集",
    "判决书",
    "会议",
    "政府",
)

# Known non-person or collective signatures that cannot be identified reliably by keywords.
MANUAL_EXCLUDE_AUTHORS = {
    "梁效",
}


def parse_records(lines: Iterable[str]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    def flush() -> None:
        if current is not None:
            records.append(current.copy())

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        match = RECORD_START.fullmatch(line)
        if match:
            flush()
            current = {"index_raw": match.group(1)}
            continue
        if current is None:
            continue
        if line.startswith(TITLE_LINE):
            current["title"] = line[len(TITLE_LINE) :]
        elif line.startswith(URL_LINE):
            current["url"] = line[len(URL_LINE) :]
        elif line.startswith(INFO_LINE):
            current["info"] = line[len(INFO_LINE) :]

    flush()
    return records


def is_single_author_page(title: str) -> bool:
    """Keep only Author:<name>, excluding subpages such as Author:X/作品集."""
    if not title.startswith(AUTHOR_PREFIX):
        return False
    author = title[len(AUTHOR_PREFIX) :].strip()
    return bool(author) and "/" not in author and "\\" not in author


def is_non_person_author(author: str) -> bool:
    normalized = author.strip()
    return (
        normalized in MANUAL_EXCLUDE_AUTHORS
        or any(keyword in normalized for keyword in NON_PERSON_KEYWORDS)
    )


def build_dataset(records: Iterable[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    converter = OpenCC("t2s")
    dataset: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    stats = {
        "records": 0,
        "kept": 0,
        "non_author_page": 0,
        "non_person_author": 0,
        "missing_field": 0,
        "duplicate": 0,
    }

    for record in records:
        stats["records"] += 1
        title = record.get("title", "")
        url = record.get("url", "")
        info = record.get("info", "")
        if not is_single_author_page(title):
            stats["non_author_page"] += 1
            continue
        author_raw = title[len(AUTHOR_PREFIX) :].strip()
        if is_non_person_author(author_raw):
            stats["non_person_author"] += 1
            continue
        if not url or not info:
            stats["missing_field"] += 1
            continue

        author = converter.convert(author_raw)
        key = (author, url)
        if key in seen:
            stats["duplicate"] += 1
            continue
        seen.add(key)
        dataset.append({"author": author, "url": url, "info": info})
        stats["kept"] += 1

    return dataset, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Kiwix text export")
    parser.add_argument("output", type=Path, help="Output JSON path")
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig") as handle:
        records = parse_records(handle)
    dataset, stats = build_dataset(records)

    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(dataset, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(json.dumps({"output": str(args.output), **stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
