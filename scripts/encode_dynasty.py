#!/usr/bin/env python3
"""Add auditable dynasty/time-bucket codes to merged author records."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


# A time bucket is an ordering key, not a claim that contemporary states were
# sequential. Parallel states share a bucket where possible.
BUCKETS: dict[int, dict[str, Any]] = {
    1: {"name": "先秦", "period": "先秦至秦统一前"},
    2: {"name": "秦汉之际", "period": "秦及西汉"},
    3: {"name": "东汉", "period": "东汉"},
    4: {"name": "三国", "period": "三国并立"},
    5: {"name": "两晋", "period": "西晋至东晋"},
    6: {"name": "南北朝前期", "period": "十六国及南北朝前期"},
    7: {"name": "南北朝后期", "period": "南北朝后期"},
    8: {"name": "隋", "period": "隋朝"},
    9: {"name": "唐前期", "period": "唐朝前期及武周"},
    10: {"name": "唐中后期", "period": "唐朝中后期"},
    11: {"name": "五代十国", "period": "五代十国并立"},
    12: {"name": "辽宋夏金前期", "period": "北宋及同期政权"},
    13: {"name": "辽宋夏金后期", "period": "南宋、金及同期政权"},
    14: {"name": "元", "period": "元朝"},
    15: {"name": "明", "period": "明朝"},
    16: {"name": "清", "period": "清朝"},
    17: {"name": "民国", "period": "民国时期"},
    18: {"name": "中华人民共和国", "period": "中华人民共和国时期"},
}

UNKNOWN = {"category": "未知", "code": -1, "bucket": None, "canonical": "未知"}
FOREIGN = {"category": "国外/非中国政权", "code": 0, "bucket": None, "canonical": None}


def _entries(bucket: int, canonical: str, *aliases: str) -> dict[str, dict[str, Any]]:
    return {
        label: {
            "category": "中国时期",
            "code": bucket,
            "bucket": bucket,
            "canonical": canonical,
        }
        for label in (canonical, *aliases)
    }


MAPPING: dict[str, dict[str, Any]] = {
    "未知": UNKNOWN,
    **_entries(1, "先秦", "夏前", "西周", "东周", "战国"),
    **_entries(2, "秦朝", "西汉"),
    **_entries(3, "东汉"),
    **_entries(4, "三国", "曹魏", "孙吴", "蜀汉"),
    **_entries(5, "两晋", "晋朝", "西晋", "东晋"),
    **_entries(6, "南北朝前期", "南北朝", "十六国", "北魏", "南梁", "刘宋", "元魏"),
    **_entries(7, "南北朝后期", "南齐", "南陈", "东魏", "西魏", "北齐", "北周"),
    **_entries(8, "隋朝"),
    **_entries(9, "唐朝前期", "唐", "武周"),
    **_entries(10, "唐朝中后期", "唐朝"),
    **_entries(11, "五代", "后梁", "后唐", "后晋", "后汉", "后周", "前蜀", "后蜀", "南唐", "吴越", "南吴", "南楚", "南汉", "北汉", "闽国", "荆南"),
    **_entries(12, "北宋", "宋朝", "辽", "西夏", "大理"),
    **_entries(13, "南宋", "金朝"),
    **_entries(14, "元朝"),
    **_entries(15, "明朝", "元末明初"),
    **_entries(16, "清朝"),
    **_entries(17, "民国"),
    **_entries(18, "中华人民共和国"),
}

FOREIGN_LABELS = {
    "日本", "朝鲜王朝", "越南陈朝", "俄罗斯", "古印度", "德国", "新罗", "法国",
    "后黎朝", "美国", "苏联", "越南", "越南李朝", "匈牙利", "北印度", "朝鲜近代", "琉球国",
    "越南胡朝", "高丽王朝", "高句丽", "东印度", "乌克兰", "保加利亚人民共和国",
    "印度", "印度尼西亚", "古希腊", "后百济", "吐蕃", "奥地利", "李朝越南",
    "苏格兰", "英国", "越南阮朝", "高丽", "阮朝",
}
MAPPING.update({label: dict(FOREIGN) for label in FOREIGN_LABELS})

# Approved manual exception: source evidence cannot determine a primary period.
REVIEWED_UNKNOWN = {
    "元朝、明朝": {
        **UNKNOWN,
        "note": "人工核查：现有记录无法确定主要活动时期，暂按未知编码 -1。",
    }
}
COMPOUND_LABELS = set(REVIEWED_UNKNOWN)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("output/merged.json"))
    parser.add_argument("--output", type=Path, default=Path("output/merged_encoded.json"))
    return parser


def transform(records: Any) -> dict[str, Any]:
    if not isinstance(records, list):
        raise ValueError("输入 JSON 顶层必须是记录数组")

    labels = Counter()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"第 {index} 条记录不是 JSON 对象")
        label = record.get("朝代")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"第 {index} 条记录缺少非空字符串字段“朝代”")
        labels[label.strip()] += 1

    compounds = sorted(set(labels) & COMPOUND_LABELS - set(REVIEWED_UNKNOWN))
    unknown_labels = sorted(set(labels) - set(MAPPING) - set(REVIEWED_UNKNOWN))
    problems = []
    if compounds:
        problems.append("复合标签待核查: " + ", ".join(compounds))
    if unknown_labels:
        problems.append("未配置映射的标签: " + ", ".join(unknown_labels))
    if problems:
        raise ValueError("\n".join(problems))

    encoded_records = []
    for record in records:
        label = record["朝代"].strip()
        mapping = MAPPING.get(label, REVIEWED_UNKNOWN.get(label))
        encoded = dict(record)
        encoded["朝代原值"] = label
        encoded["朝代类别"] = mapping["category"]
        encoded["朝代编码"] = mapping["code"]
        encoded["年代排序"] = mapping["bucket"]
        encoded["朝代id"] = mapping["bucket"] if mapping["bucket"] is not None else mapping["code"]
        encoded_records.append(encoded)

    return {
        "metadata": {
            "source": "output/merged.json",
            "record_count": len(encoded_records),
            "encoding_version": "1.0",
            "encoding_policy": "朝代原值显式映射；朝代id沿用年代时间桶；未知=-1；国外/非中国政权=0；中国时期按时间桶排序；并行政权可共享时间桶",
        },
        "编码规则映射": {
            label: {**mapping, "frequency": labels[label]}
            for label, mapping in sorted({**MAPPING, **REVIEWED_UNKNOWN}.items())
            if label in labels
        },
        "年代时间桶": BUCKETS,
        "records": encoded_records,
    }


def write_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
            suffix=".tmp", delete=False,
        ) as temp:
            temp_name = temp.name
            json.dump(payload, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    args = build_parser().parse_args()
    try:
        with args.input.open("r", encoding="utf-8") as source:
            records = json.load(source)
        payload = transform(records)
        write_atomically(args.output, payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"错误：{error}")
        return 1

    print(f"已编码 {payload['metadata']['record_count']} 条记录 -> {args.output}")
    print(f"映射标签数：{len(payload['编码规则映射'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
