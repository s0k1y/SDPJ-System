"""内置数据集加载器

优化策略：
1. system_meta 标记：二次启动直接跳过，零文件读取
2. manifest.json 预计算清单：替代运行时逐行计数
3. 单次遍历：合并计数和解析为一次文件读取
4. asyncio.to_thread：文件 I/O 不阻塞事件循环
5. 原生 SQL 批量插入：绕过 ORM 层提升写入性能
"""
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Optional

_BASE = Path(__file__).parent
_MANIFEST_PATH = _BASE / "manifest.json"
_LOADED_KEY = "builtin_datasets_loaded"


def _load_manifest() -> Optional[dict]:
    if not _MANIFEST_PATH.exists():
        return None
    try:
        return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_and_parse_jsonl(
    jsonl_file: Path,
) -> tuple[int, list[tuple[str, str, int]], Optional[int]]:
    """单次遍历读取 jsonl 文件，同时完成行计数和 JSON 解析。

    Returns:
        (line_count, records, dataset_id_placeholder)
        dataset_id 占位为 0，由调用方替换。
    """
    line_count = 0
    records: list[tuple[str, str, int]] = []
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line_count += 1
            try:
                s = json.loads(line)
                records.append((s["subtype"], s["poc"], 0))
            except Exception:
                pass
    return line_count, records


def _compute_file_md5(file_path: Path) -> str:
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


async def load_builtin_datasets(sample_db, force_reload: bool = False) -> None:
    """加载内置数据集，保留完整的目录层级结构

    优化流程：
    1. 若 system_meta 中 builtin_datasets_loaded=True 且非强制重载，直接返回
    2. 对每个 jsonl 文件：
       a. 优先从 manifest.json 获取行数（MD5 校验）
       b. manifest 不可用时回退单次遍历计数+解析
       c. 幂等检查：已存在且行数一致则跳过
       d. 使用原生 SQL 批量插入
    3. 全部加载完成后写入 system_meta 标记
    """
    if not force_reload:
        loaded = await sample_db.get_system_meta(_LOADED_KEY)
        if loaded == "True":
            return

    manifest = _load_manifest()

    for jsonl_file in sorted(_BASE.rglob("*.jsonl")):
        relative_path = jsonl_file.relative_to(_BASE)
        rel_str = str(relative_path).replace("\\", "/")
        dataset_name = f"builtin_datasets/{relative_path.with_suffix('')}"
        risk_type = jsonl_file.parent.name

        file_line_count: int | None = None
        records: list[tuple[str, str, int]] | None = None

        if manifest is not None and rel_str in manifest:
            entry = manifest[rel_str]
            current_md5 = await asyncio.to_thread(_compute_file_md5, jsonl_file)
            if current_md5 == entry["md5"]:
                file_line_count = entry["lines"]

        if file_line_count is None:
            lc, recs = await asyncio.to_thread(_read_and_parse_jsonl, jsonl_file)
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
            sample_count = await sample_db.get_sample_count_by_dataset(dataset_id)
            if sample_count == file_line_count:
                continue
            await sample_db.delete_samples_by_dataset(dataset_id)

        if records is None:
            _, records = await asyncio.to_thread(_read_and_parse_jsonl, jsonl_file)

        records = [(r[0], r[1], dataset_id) for r in records]

        if records:
            await sample_db.bulk_insert_samples(records)

    await sample_db.set_system_meta(_LOADED_KEY, "True")
