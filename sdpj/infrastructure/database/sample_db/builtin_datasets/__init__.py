"""内置数据集加载器.

优化策略:
1. SystemMeta 快速跳过:manifest 未变时完全跳过加载
2. 增量检测:manifest 变化时逐文件比对行数,仅重新加载变化的文件
3. 单次遍历:合并计数和解析为一次文件读取
4. asyncio.to_thread:文件 I/O 不阻塞事件循环
5. 原生 SQL 批量插入:绕过 ORM 层提升写入性能
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, cast  # noqa: F401

_BASE = Path(__file__).parent
_MANIFEST_PATH = _BASE / "manifest.json"
_LOADED_KEY = "builtin_datasets_loaded"


def _load_manifest() -> dict | None:
    if not _MANIFEST_PATH.exists():
        return None
    try:
        return cast("dict", json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def _read_and_parse_jsonl(
    jsonl_file: Path,
) -> tuple[int, list[tuple[str, str, int]], int | None]:
    """单次遍历读取 jsonl 文件,同时完成行计数和 JSON 解析..

    Returns:
        (line_count, records, dataset_id_placeholder)
        dataset_id 占位为 0,由调用方替换.

    """
    line_count = 0
    records: list[tuple[str, str, int]] = []
    with open(jsonl_file, encoding="utf-8") as f:  # noqa: PTH123
        for line in f:
            line = line.strip()  # noqa: PLW2901
            if not line:
                continue
            line_count += 1
            try:
                s = json.loads(line)
                records.append((s["subtype"], s["poc"], 0))
            except Exception:  # noqa: BLE001, S110
                pass
    return line_count, records, None


async def load_builtin_datasets(sample_db, force_reload: bool = False) -> None:  # noqa: ANN001, C901, FBT001, FBT002, PLR0912
    """加载内置数据集,保留完整的目录层级结构.

    增量加载流程:
    1. 若非强制重载,比对 SystemMeta 中存储的 manifest 与当前 manifest
       - 一致则完全跳过(所有数据集已加载且未变)
    2. manifest 不一致时逐文件检查:
       a. 从 manifest.json 获取期望行数
       b. 用 SELECT COUNT(*) 比对数据库实际行数
       c. 行数一致则跳过,不一致则删除旧样本重新插入
    3. 加载完成后将当前 manifest 写入 SystemMeta
    """
    manifest = _load_manifest()

    if not force_reload and manifest is not None:
        stored = await sample_db.get_system_meta(_LOADED_KEY)
        if stored is not None:
            try:
                stored_manifest = json.loads(stored)
                if stored_manifest == manifest:
                    return
            except (json.JSONDecodeError, TypeError):
                pass

    for jsonl_file in sorted(_BASE.rglob("*.jsonl")):
        relative_path = jsonl_file.relative_to(_BASE)
        rel_str = str(relative_path).replace("\\", "/")
        dataset_name = f"builtin_datasets/{relative_path.with_suffix('')}"
        risk_type = jsonl_file.parent.name

        file_line_count: int | None = None
        records: list[tuple[str, str, int]] | None = None

        if manifest is not None and rel_str in manifest:
            file_line_count = manifest[rel_str]["lines"]

        if file_line_count is None:
            lc, recs, _ = await asyncio.to_thread(_read_and_parse_jsonl, jsonl_file)
            file_line_count = lc
            records = recs

        dataset_id: int | None = None
        try:
            dataset_id = await sample_db.create_dataset(dataset_name, risk_type)
        except ValueError:
            existing = await sample_db.get_dataset_by_name(dataset_name)
            if existing is None:
                continue
            dataset_id = existing["dataset_id"]
            if not force_reload:
                sample_count = await sample_db.get_sample_count_by_dataset(dataset_id)
                if sample_count == file_line_count:
                    continue
            await sample_db.delete_samples_by_dataset(dataset_id)

        if records is None:
            _, records, _ = await asyncio.to_thread(_read_and_parse_jsonl, jsonl_file)

        assert records is not None  # noqa: S101
        assert dataset_id is not None  # noqa: S101
        records = [(r[0], r[1], dataset_id) for r in records]

        if records:
            await sample_db.bulk_insert_samples(records)

    if manifest is not None:
        await sample_db.set_system_meta(_LOADED_KEY, json.dumps(manifest, ensure_ascii=False))
