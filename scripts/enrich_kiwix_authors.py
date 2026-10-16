#!/usr/bin/env python3
"""Batch-enrich Kiwix authors through the local FlexLLM API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("资料/kiwix-authors-person.json")
DEFAULT_SETTINGS = Path("/Users/yeechao/Desktop/shell/AIPlugins/OPENAI/flex_llm/configs/settings.yaml")
DEFAULT_URL = "http://127.0.0.1:8000/v1/chat/completions"
DEFAULT_OUTPUT_DIR = Path("output")
OUTPUT_FIELDS = ["id", "author", "url", "朝代", "领域", "身份与贡献", "影响力评分", "简介", "备注"]
DYNASTIES = [
    "夏前", "夏朝", "商朝", "西周", "东周", "秦朝", "西汉", "新朝", "玄汉", "东汉",
    "曹魏", "蜀汉", "孙吴", "西晋", "东晋", "十六国", "刘宋", "南齐", "南梁", "南陈",
    "北魏", "东魏", "北齐", "西魏", "北周", "隋朝", "唐朝前期", "武周", "唐朝中后期",
    "后梁", "后唐", "后晋", "后汉", "后周", "南吴", "南唐", "前蜀", "后蜀", "南汉",
    "南楚", "吴越", "闽国", "荆南", "北汉", "北宋", "南宋", "辽朝", "西夏", "金朝",
    "元朝", "明朝", "清朝", "民国", "中华人民共和国", "未知",
]

SYSTEM_PROMPT = """你是历史人物元数据整理助手。根据输入记录的 author 和 info，生成简明、适合表格速查的作者元数据。
必须遵守：
- 只根据输入内容，不得虚构生平、作品、年代或影响。
- 每个输入必须恰好对应一个输出；id 和 author 必须原样返回；url 由调用程序补入，不要生成。
- 朝代只能选给定枚举中的一个具体政权，不得填南朝、三国、五代十国等上位时期。
- 朝代字段表示作者主要创作、任职或产生历史影响的时期，不是出生时所在政权；跨政权人物选主要活动时期并在备注注明跨期。近现代人物按主要活动年代归入清朝、民国或中华人民共和国，不得仅因跨越政权而填未知。例如胡适归民国。
- “唐”必须按主要活动年代细分为“唐朝前期”或“唐朝中后期”，不得直接输出“唐”。
- 只有资料确实不足以判断主要活动政权时才填未知，并在备注说明资料缺口。
- 领域、身份与贡献、简介未知时填“未知”；简介限一句话。
- 影响力评分必须是1至5的整数，表示该人物在其领域的历史影响，不代表道德或作品质量：1仅零星记载；2有明确身份或活动记录；3有可辨认领域贡献；4有显著影响；5广泛公认的代表人物。资料很少也需评分，并在备注写“资料有限，暂定”。
- 备注只写异说、资料局限、朝代判定理由或评分依据说明；无备注写空字符串。
- 严格按提供的 JSON Schema 输出。"""


def make_schema(batch: list[dict[str, str]], batch_id: str) -> dict[str, Any]:
    item_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "author", "朝代", "领域", "身份与贡献", "影响力评分", "简介", "备注"],
        "properties": {
            "id": {"type": "string", "enum": [row["id"] for row in batch]},
            "author": {"type": "string"},
            "朝代": {"type": "string", "enum": DYNASTIES},
            "领域": {"type": "string"},
            "身份与贡献": {"type": "string"},
            "影响力评分": {"type": "integer", "minimum": 1, "maximum": 5},
            "简介": {"type": "string"},
            "备注": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["batch_id", "records"],
        "properties": {
            "batch_id": {"type": "string", "enum": [batch_id]},
            "records": {"type": "array", "items": item_schema},
        },
    }


def load_records(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("输入 JSON 顶层必须是数组")
    result = []
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"第 {index} 条记录不是对象")
        for field in ("author", "url", "info"):
            if not isinstance(row.get(field), str):
                raise ValueError(f"第 {index} 条记录缺少字符串字段 {field}")
        result.append({"id": str(index), "author": row["author"], "url": row["url"], "info": row["info"]})
    return result


def validate_record(row: dict[str, Any]) -> None:
    if set(row) != set(OUTPUT_FIELDS):
        raise ValueError("输出字段不符合约定")
    if not all(isinstance(row[field], str) for field in ("id", "author", "url")):
        raise ValueError("id、author、url 必须为字符串")
    if row["朝代"] not in DYNASTIES:
        raise ValueError(f"非法朝代：{row['朝代']}")
    for field in ("领域", "身份与贡献", "简介", "备注"):
        if not isinstance(row[field], str):
            raise ValueError(f"{field} 必须是字符串")
    if type(row["影响力评分"]) is not int or not 1 <= row["影响力评分"] <= 5:
        raise ValueError("影响力评分必须是1—5整数")


def decode_json_text(text: str) -> Any:
    candidate = text.strip()
    if candidate.startswith("```json"):
        candidate = candidate[7:]
    elif candidate.startswith("```"):
        candidate = candidate[3:]
    if candidate.endswith("```"):
        candidate = candidate[:-3]
    try:
        return json.loads(candidate.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型回复不是完整 JSON（长度 {len(text)} 字符）：{exc}") from exc


def decode_reply(envelope: dict[str, Any], protocol: str) -> Any:
    if protocol == "openai":
        try:
            content = envelope["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenAI 兼容接口没有返回 choices[0].message.content") from exc
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not isinstance(content, str):
            raise ValueError("OpenAI 兼容接口返回的 content 不是字符串")
        return decode_json_text(content)
    data = envelope.get("data")
    if isinstance(data, dict):
        return data
    reply = envelope.get("reply", "")
    if not isinstance(reply, str):
        raise ValueError("旧版 FlexLLM 网关没有返回可解析的 data/reply")
    return decode_json_text(reply)


def validate_batch(data: Any, batch: list[dict[str, str]], batch_id: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("响应批次结构不正确")
    returned_batch_id = data.get("batch_id")
    if returned_batch_id not in (batch_id, batch_id.split(".")[0]):
        raise ValueError(f"响应 batch_id 不匹配：期望 {batch_id}，实际 {returned_batch_id}")
    expected = {row["id"]: row for row in batch}
    output: dict[str, dict[str, Any]] = {}
    for row in data["records"]:
        if not isinstance(row, dict):
            raise ValueError("records 中包含非对象")
        record_id = row.get("id")
        if record_id not in expected:
            raise ValueError(f"响应中出现未知 id：{record_id}")
        source = expected[record_id]
        normalized = {field: row.get(field) for field in OUTPUT_FIELDS if field != "url"}
        normalized["url"] = source["url"]
        if normalized.get("朝代") == "唐":
            normalized["朝代"] = "唐朝前期" if any(term in source["info"] for term in ("玄宗", "开元", "天宝")) else "唐朝中后期"
        validate_record(normalized)
        if normalized["author"] != source["author"]:
            raise ValueError(f"id={record_id} 的 author 与输入不匹配")
        if record_id in output:
            raise ValueError(f"响应中 id 重复：{record_id}")
        output[record_id] = normalized
    if set(output) != set(expected):
        missing = sorted(set(expected) - set(output), key=int)
        raise ValueError(f"响应记录不完整，缺少 id：{missing}")
    return [output[row["id"]] for row in batch]


def normalize_openai_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions") or normalized.endswith("/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def detect_protocol(url: str, requested: str) -> str:
    if requested != "auto":
        return requested
    return "openai" if "/chat/completions" in url or url.rstrip("/").endswith("/completions") else "flexllm"


def post_batch(url: str, protocol: str, provider: str, model: str | None, config_path: Path | None, api_key: str | None, batch: list[dict[str, str]], batch_id: str, timeout: int) -> list[dict[str, Any]]:
    prompt_records = [{"id": row["id"], "author": row["author"], "info": row["info"]} for row in batch]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"batch_id": batch_id, "records": prompt_records}, ensure_ascii=False)},
    ]
    if protocol == "openai":
        if not model:
            raise ValueError("OpenAI 兼容接口必须通过 --model 或 OPENAI_MODEL 指定模型")
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 24000,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    else:
        if config_path is None:
            raise ValueError("旧版 FlexLLM 协议必须提供 --settings")
        request_body = {
            "provider": provider,
            "config_path": str(config_path),
            "messages": messages,
            "temperature": 0,
            "max_tokens": 24000,
            "timeout": timeout,
            "json_schema": make_schema(batch, batch_id),
        }
        if model:
            request_body["model"] = model
        headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout + 15) as response:
        envelope = json.loads(response.read().decode("utf-8"))
    if protocol == "flexllm" and not envelope.get("ok"):
        raise RuntimeError(f"旧版 FlexLLM 网关返回失败：{envelope}")
    return validate_batch(decode_reply(envelope, protocol), batch, batch_id)


def post_batch_resilient(url: str, protocol: str, provider: str, model: str | None, config_path: Path | None, api_key: str | None, batch: list[dict[str, str]], batch_id: str, timeout: int, min_chunk_size: int = 8) -> list[dict[str, Any]]:
    """Try one request first, then subdivide a failed batch without partial commits."""
    try:
        return post_batch(url, protocol, provider, model, config_path, api_key, batch, batch_id, timeout)
    except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        if len(batch) <= min_chunk_size:
            raise RuntimeError(f"子批次 {batch_id}（{len(batch)} 条）仍失败：{exc}") from exc
        midpoint = len(batch) // 2
        left, right = batch[:midpoint], batch[midpoint:]
        print(f"批次 {batch_id} 的 {len(batch)} 条请求失败，自动拆成 {len(left)}+{len(right)} 条重试：{exc}", file=sys.stderr, flush=True)
        left_result = post_batch_resilient(url, protocol, provider, model, config_path, api_key, left, f"{batch_id}.a", timeout, min_chunk_size)
        right_result = post_batch_resilient(url, protocol, provider, model, config_path, api_key, right, f"{batch_id}.b", timeout, min_chunk_size)
        return left_result + right_result


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量生成 Kiwix 作者元数据，支持 OpenAI 兼容接口和旧版 FlexLLM 网关")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--settings", type=Path, default=Path(os.environ.get("FLEXLLM_SETTINGS", str(DEFAULT_SETTINGS))))
    parser.add_argument("--url", default=os.environ.get("AUTHOR_LLM_URL", DEFAULT_URL), help="完整聊天接口 URL；也可用 AUTHOR_LLM_URL")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"), help="OpenAI 兼容服务根地址；自动补上 /chat/completions，也可用 OPENAI_BASE_URL")
    parser.add_argument("--protocol", choices=("auto", "openai", "flexllm"), default="auto", help="接口协议，默认按 URL 自动判断")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"), help="OpenAI 兼容接口 Bearer token，也可用 OPENAI_API_KEY")
    parser.add_argument("--provider", default="huoshan", help="仅旧版 FlexLLM 协议使用；默认 huoshan")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL"), help="模型名；OpenAI 兼容接口必填，也可用 OPENAI_MODEL")
    parser.add_argument("--concurrency", type=int, default=1, help="并发批次数，默认1")
    parser.add_argument("--range", dest="batch_range", help="批次范围，如 1,2-5,8；省略时使用默认范围")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--max-chars", type=int, default=50000)
    parser.add_argument("--timeout", type=int, default=280)
    parser.add_argument("--start-batch", type=int, default=1, help="恢复起始批次，序号从1开始")
    parser.add_argument("--end-batch", type=int, help="最后批次（含）；省略时处理到末尾")
    parser.add_argument("--only-batch", type=int, help="仅处理指定批次，已存在时不覆盖，除非指定 --force")
    parser.add_argument("--force", action="store_true", help="覆盖目标批次的已有 JSON 文件")
    parser.add_argument("--dry-run", action="store_true", help="只预览批次和待处理状态，不调用模型")
    parser.add_argument("--pause", type=float, default=0.5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size != 50:
        raise SystemExit("按要求固定每批50条；不支持更改 --batch-size")
    if args.max_chars < 1000 or args.timeout < 1 or args.timeout > 300 or args.pause < 0:
        raise SystemExit("max-chars 至少1000；timeout须为1—300秒；pause不得为负")
    if args.concurrency < 1:
        raise SystemExit("--concurrency 必须大于等于1")
    if args.start_batch < 1 or (args.end_batch is not None and args.end_batch < args.start_batch):
        raise SystemExit("批次范围无效")
    if args.only_batch is not None and args.only_batch < 1:
        raise SystemExit("--only-batch 必须大于等于1")
    if args.base_url:
        args.url = normalize_openai_url(args.base_url)
    protocol = detect_protocol(args.url, args.protocol)
    if not args.input.is_file():
        raise SystemExit(f"输入文件不存在：{args.input}")
    if protocol == "flexllm" and not args.settings.is_file():
        raise SystemExit(f"旧版 FlexLLM settings 配置不存在：{args.settings}")
    if protocol == "openai" and not args.model:
        raise SystemExit("OpenAI 兼容接口必须指定 --model 或设置 OPENAI_MODEL")

    if protocol == "flexllm" and args.model is None:
        try:
            import yaml
        except ImportError as exc:
            raise SystemExit("读取 settings 中的默认模型需要 PyYAML；请安装 pyyaml 或显式指定 --model") from exc
        settings = yaml.safe_load(args.settings.read_text(encoding="utf-8")) or {}
        provider_config = settings.get(args.provider, {}) if isinstance(settings, dict) else {}
        if isinstance(provider_config, dict):
            configured_model = provider_config.get("model")
            args.model = str(configured_model) if configured_model else None

    records = load_records(args.input)
    input_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    batches = [records[i:i + 50] for i in range(0, len(records), 50)]
    if args.batch_range:
        if args.only_batch is not None or args.start_batch != 1 or args.end_batch is not None:
            raise SystemExit("--range 不能与 --only-batch、--start-batch 或 --end-batch 同时使用")
        chosen_set: set[int] = set()
        try:
            for part in args.batch_range.split(","):
                part = part.strip()
                if not part:
                    raise ValueError("空范围项")
                if "-" in part:
                    start_text, end_text = part.split("-", 1)
                    start, end = int(start_text), int(end_text)
                    if start < 1 or end < start:
                        raise ValueError("范围起止值无效")
                    chosen_set.update(range(start, end + 1))
                else:
                    number = int(part)
                    if number < 1:
                        raise ValueError("批次必须大于等于1")
                    chosen_set.add(number)
        except ValueError as exc:
            raise SystemExit(f"--range 格式无效：{exc}") from exc
        chosen = sorted(chosen_set)
    elif args.only_batch is not None:
        chosen = [args.only_batch]
    else:
        last = min(args.end_batch or len(batches), len(batches))
        chosen = list(range(args.start_batch, last + 1))
    invalid = [number for number in chosen if number > len(batches)]
    if invalid:
        raise SystemExit(f"批次超出范围：{invalid}；总批次数 {len(batches)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("input_sha256") != input_hash or manifest.get("batch_size") != 50:
            raise SystemExit("manifest 与当前输入文件不匹配；请指定新的 --output-dir，避免混用批次结果")
    else:
        manifest = {"input": str(args.input), "input_sha256": input_hash, "batch_size": 50, "total_records": len(records), "total_batches": len(batches), "completed_batches": []}
        atomic_write_json(manifest_path, manifest)

    pending = []
    for number in chosen:
        path = args.output_dir / f"batch_{number:04d}.json"
        if path.exists() and not args.force:
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                expected_rows = batches[number - 1]
                if saved.get("batch_number") == number and len(saved.get("records", [])) == len(expected_rows):
                    print(f"跳过已完成批次 {number}: {path}")
                    continue
            except (json.JSONDecodeError, AttributeError):
                pass
            raise SystemExit(f"批次文件已存在但无法校验：{path}；检查后用 --force 定点重做")
        pending.append(number)

    print(f"输入记录: {len(records)}；总批次: {len(batches)}；本次选择: {chosen}；待请求: {pending}")
    print(f"protocol: {protocol}；url: {args.url}；model: {args.model or 'settings 默认'}；并发: {args.concurrency}")
    if args.dry_run:
        for number in pending:
            batch = batches[number - 1]
            chars = sum(len(row["info"]) + len(row["author"]) + 100 for row in batch)
            print(f"批次 {number}: {len(batch)} 条，id {batch[0]['id']}..{batch[-1]['id']}，估算输入字符 {chars}")
        return 0

    def process_batch(number: int) -> tuple[int, list[dict[str, Any]]]:
        batch = batches[number - 1]
        batch_id = f"{number:04d}"
        print(f"请求批次 {number}/{len(batches)}（{len(batch)} 条）", flush=True)
        result = post_batch_resilient(args.url, protocol, args.provider, args.model, args.settings if protocol == "flexllm" else None, args.api_key, batch, batch_id, args.timeout)
        return number, result

    manifest_lock = threading.Lock()

    def save_batch(number: int, result: list[dict[str, Any]]) -> None:
        output_path = args.output_dir / f"batch_{number:04d}.json"
        atomic_write_json(output_path, {"batch_number": number, "batch_id": f"{number:04d}", "records": result})
        with manifest_lock:
            done = set(manifest.get("completed_batches", []))
            done.add(number)
            manifest["completed_batches"] = sorted(done)
            atomic_write_json(manifest_path, manifest)
        print(f"已写入 {output_path}，{len(result)} 条校验通过")

    try:
        if args.concurrency == 1:
            for position, number in enumerate(pending, 1):
                number, result = process_batch(number)
                save_batch(number, result)
                if args.pause and position < len(pending):
                    time.sleep(args.pause)
        else:
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = {executor.submit(process_batch, number): number for number in pending}
                for future in as_completed(futures):
                    number = futures[future]
                    try:
                        completed_number, result = future.result()
                    except Exception as exc:
                        for other in futures:
                            other.cancel()
                        raise RuntimeError(f"批次 {number} 失败：{exc}") from exc
                    save_batch(completed_number, result)
    except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        failed_number = locals().get("number", pending[0] if pending else "未知")
        print(f"本批未落盘；此前成功批次保留。可用 --start-batch {failed_number} 或 --only-batch {failed_number} 恢复。错误：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
