#!/usr/bin/env python3
"""Classify domain strings into auditable multi-label IDs without editing input."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

# Fixed IDs: stable across runs; never generated from observed frequencies.
LABELS = {
    101: ("文学与语言", "文学"), 102: ("文学与语言", "诗歌"), 103: ("文学与语言", "词"),
    104: ("文学与语言", "散曲"), 105: ("文学与语言", "辞赋"), 106: ("文学与语言", "小说"),
    107: ("文学与语言", "戏曲戏剧"), 108: ("文学与语言", "文章文体"), 109: ("文学与语言", "文学批评"),
    110: ("文学与语言", "翻译"), 111: ("文学与语言", "语言文字"),
    201: ("历史与文献", "史学历史"), 202: ("历史与文献", "地方志"), 203: ("历史与文献", "碑铭金石"),
    204: ("历史与文献", "目录文献编纂"), 205: ("历史与文献", "考古"), 206: ("历史与文献", "地理"),
    301: ("哲学与思想", "哲学"), 302: ("哲学与思想", "思想"), 303: ("哲学与思想", "儒学经学"),
    304: ("哲学与思想", "理学易学"), 305: ("哲学与思想", "逻辑"),
    401: ("政治与公共事务", "政治政务"), 402: ("政治与公共事务", "政论"), 403: ("政治与公共事务", "外交"),
    404: ("政治与公共事务", "法律司法"), 405: ("政治与公共事务", "礼制制度"),
    406: ("政治与公共事务", "奏议公文"), 407: ("政治与公共事务", "社会运动"),
    408: ("政治与公共事务", "经济财政"),
    501: ("军事与战略", "军事"), 502: ("军事与战略", "兵学战略"),
    601: ("宗教与信仰", "宗教"), 602: ("宗教与信仰", "佛教"), 603: ("宗教与信仰", "道教"),
    604: ("宗教与信仰", "宗教研究"), 605: ("宗教与信仰", "传教"),
    701: ("教育与学术", "教育"), 702: ("教育与学术", "学术研究"), 703: ("教育与学术", "科举"),
    801: ("科学与技术", "医学"), 802: ("科学与技术", "农学"), 803: ("科学与技术", "数学"),
    804: ("科学与技术", "天文历法"), 805: ("科学与技术", "水利"), 806: ("科学与技术", "建筑"),
    807: ("科学与技术", "生物自然科学"), 808: ("科学与技术", "博物"),
    901: ("艺术与文化", "书法"), 902: ("艺术与文化", "绘画书画"), 903: ("艺术与文化", "音乐"),
    904: ("艺术与文化", "艺术理论"), 905: ("艺术与文化", "民俗茶文化"), 906: ("艺术与文化", "文物鉴赏"),
    1001: ("经济与社会", "经济商业"), 1002: ("经济与社会", "出版"), 1003: ("经济与社会", "新闻传播"),
    1004: ("经济与社会", "社会学"), 1005: ("经济与社会", "公共卫生慈善"),
    9001: ("身份标签", "官员"), 9002: ("身份标签", "君主"), 9003: ("身份标签", "作者"),
    9004: ("身份标签", "学者"), 9005: ("身份标签", "僧人"), 9006: ("身份标签", "将领"),
    9999: ("未知/待分类", "未知"),
}

# Exact atomic phrase mappings. Separators are handled before phrase matching.
ALIASES = {
    "文学": [101], "诗歌": [102], "诗词": [102, 103], "诗文": [101], "诗": [102],
    "汉诗": [102], "和歌": [102], "词": [103], "词学": [103, 109], "散曲": [104],
    "辞赋": [105], "赋": [105], "辞赋": [105], "小说": [106], "笔记小说": [106, 108],
    "戏曲": [107], "戏剧": [107], "传奇": [107, 106], "文学批评": [109], "文学评论": [109],
    "诗论": [109], "词论": [109], "文学理论": [109], "评论": [109], "古文": [108],
    "文章": [108], "文辞": [108], "文书": [108], "公文": [406], "文书": [108, 406],
    "制诰": [406, 108], "奏议": [406], "奏疏": [406], "奏表": [406], "奏状": [406],
    "政务": [401], "政治": [401], "政务与文辞": [401, 108], "政论": [402], "政论文": [402],
    "时事评论": [402], "政治评论": [402], "思想": [302], "哲学": [301], "哲学与寓言": [301],
    "逻辑": [305], "政治思想": [302, 401], "政治经济学": [408, 301],
    "史学": [201], "历史": [201], "历史学": [201], "文史": [201], "史论": [201, 402],
    "史地": [201, 206], "历史地理": [201, 206], "地方志": [202], "方志": [202], "地志": [202],
    "碑铭": [203], "碑刻": [203], "碑志": [203], "碑文": [203], "碑记": [203], "碑文": [203],
    "墓志": [203], "墓志文": [203], "金石": [203], "金石学": [203], "铭文": [203],
    "目录学": [204], "文献学": [204], "文献": [204], "文献整理": [204], "编纂": [204],
    "校勘": [204], "版本学": [204], "藏书": [204], "古籍研究": [204], "典籍整理": [204],
    "考据": [204], "考古": [205], "地理": [206], "地理学": [206], "海洋": [206],
    "经学": [303], "儒学": [303], "儒家": [303], "易学": [304], "理学": [304], "礼学": [303],
    "法律": [404], "法学": [404], "司法": [404], "法医学": [801, 404], "法制": [404],
    "法律文书": [404, 406], "判文": [404, 406], "判词": [404, 406], "官箴与判文": [404, 406],
    "礼制": [405], "礼乐": [405], "制度": [405], "典章制度": [405], "外交": [403], "外交史": [201, 403],
    "军事": [501], "军事学": [501], "军事文书": [501, 406], "兵学": [502], "兵法": [502],
    "佛教": [602], "佛学": [602], "佛学研究": [604, 602], "道教": [603], "宗教": [601],
    "宗教研究": [604], "宗教史": [604, 201], "译经": [602, 110], "佛经翻译": [602, 110],
    "佛教翻译": [602, 110], "佛教译经": [602, 110], "佛教译著": [602, 110], "翻译": [110],
    "教育": [701], "启蒙教育": [701], "蒙学": [701], "学术": [702], "科举": [703],
    "经学": [303], "文字学": [111], "语言文字": [111], "语言学": [111], "音韵学": [111],
    "训诂": [111], "书法": [901], "绘画": [902], "书画": [901, 902], "音乐": [903],
    "音乐学": [903], "艺术理论": [904], "艺术史": [904], "美术": [904], "美术史": [904],
    "民俗": [905], "民俗学": [905], "茶文化": [905], "茶学": [905], "文物鉴赏": [906],
    "医学": [801], "医术": [801], "中医": [801], "本草学": [801], "养生": [801], "公共卫生": [1005],
    "农学": [802], "农业": [802], "数学": [803], "天文": [804], "天文学": [804], "历法": [804],
    "天文历法": [804], "天文历算": [804], "水利": [805], "建筑": [806], "生物学": [807],
    "植物学": [807], "生态学": [807], "自然科学": [807], "科学": [807], "科学技术": [807], "博物": [808], "博物学": [808],
    "经济": [1001], "经济学": [1001], "财政": [1001], "商业": [1001], "实业": [1001], "出版": [1002],
    "新闻": [1003], "新闻传播": [1003], "社会学": [1004], "社会理论": [1004], "社会思想": [1004],
    "慈善": [1005], "工人运动": [407], "工运": [407], "劳工运动": [407], "妇女运动": [407],
    "社会运动": [407], "革命": [407], "未知": [9999],
    "官员": [9001], "皇帝": [9002], "君主": [9002], "作者": [9003], "学者": [9004], "僧人": [9005], "将领": [9006],
}

# Free-standing descriptors that denote roles, not subject domains.
ROLE_WORDS = {"官员": 9001, "皇帝": 9002, "君主": 9002, "作者": 9003, "学者": 9004, "僧人": 9005, "将领": 9006}
SPLIT_RE = re.compile(r"[、/；;，,与和及]+")


def classify(value: str) -> tuple[list[int], list[int], list[str]]:
    domain_ids: set[int] = set()
    identity_ids: set[int] = set()
    unmatched: list[str] = []
    if value.strip() == "未知":
        return [9999], [], []
    # Remove explanatory parenthetical wrappers but retain their content for matching.
    parts = [p.strip() for p in SPLIT_RE.split(value.strip()) if p.strip()]
    for part in parts:
        part = re.sub(r"^[（(]|[）)]$", "", part).strip()
        ids = ALIASES.get(part)
        if ids is None:
            # Exact phrase containment is accepted only if it resolves to one unique label set.
            hits = [(phrase, codes) for phrase, codes in ALIASES.items() if phrase and phrase in part]
            if hits:
                covered = "".join(phrase for phrase, _ in hits)
                best_len = max(len(phrase) for phrase, _ in hits)
                best = {tuple(codes) for phrase, codes in hits if len(phrase) == best_len}
                if len(best) == 1 and best_len >= 2:
                    ids = list(next(iter(best)))
        if ids is None:
            unmatched.append(part)
            continue
        for code in ids:
            if code >= 9000 and code != 9999:
                identity_ids.add(code)
            else:
                domain_ids.add(code)
    return sorted(domain_ids), sorted(identity_ids), unmatched


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as f:
            tmp = f.name
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("output/merged_encoded.json"))
    parser.add_argument("--output", type=Path, default=Path("output/merged_domain_encoded.json"))
    parser.add_argument("--review", type=Path, default=Path("output/domain_review.csv"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as f:
        source = json.load(f)
    records = source.get("records")
    if not isinstance(records, list):
        raise SystemExit("输入文件缺少 records 数组")

    frequencies = Counter()
    classifications: dict[str, tuple[list[int], list[int], list[str]]] = {}
    for i, record in enumerate(records):
        value = record.get("领域")
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"记录索引 {i} 的领域不是非空字符串")
        value = value.strip()
        frequencies[value] += 1
        classifications.setdefault(value, classify(value))

    patched = []
    for record in records:
        value = record["领域"].strip()
        domain_ids, identity_ids, unmatched = classifications[value]
        item = dict(record)
        item["领域标签"] = [f"{LABELS[c][0]}/{LABELS[c][1]}" for c in domain_ids]
        item["领域编码"] = domain_ids
        item["身份标签"] = [LABELS[c][1] for c in identity_ids]
        item["身份编码"] = identity_ids
        item["领域分类状态"] = "未知" if domain_ids == [9999] and not unmatched else ("待审核" if unmatched else "已分类")
        item["领域待审核片段"] = unmatched
        patched.append(item)

    payload = {
        "metadata": {"source": str(args.input), "record_count": len(patched), "domain_taxonomy_version": "1.0", "unclassified_policy": "未匹配片段不猜测，保留并标记待审核；未知使用9999"},
        "领域编码规则映射": {str(k): {"一级分类": v[0], "二级标签": v[1]} for k, v in sorted(LABELS.items())},
        "records": patched,
    }
    atomic_write_json(args.output, payload)

    with args.review.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["领域原值", "频数", "候选领域标签（一级/二级；分号分隔）", "候选领域编码（分号分隔）", "身份标签（分号分隔）", "未匹配片段", "分类状态", "审核备注"])
        for value, count in sorted(frequencies.items(), key=lambda x: (-x[1], x[0])):
            domain_ids, identity_ids, unmatched = classifications[value]
            tags = [f"{LABELS[c][0]}/{LABELS[c][1]}" for c in domain_ids]
            status = "未知" if domain_ids == [9999] and not unmatched else ("待审核" if unmatched else "已分类")
            writer.writerow([value, count, ";".join(tags), ";".join(map(str, domain_ids)), ";".join(LABELS[c][1] for c in identity_ids), ";".join(unmatched), status, ""])

    states = Counter(r["领域分类状态"] for r in patched)
    print(f"records={len(patched)} unique_values={len(frequencies)} statuses={dict(states)}")
    print(f"output={args.output} review={args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
