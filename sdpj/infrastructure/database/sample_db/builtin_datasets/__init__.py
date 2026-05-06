"""内置数据集加载器"""
import json
from pathlib import Path

_BASE = Path(__file__).parent


async def load_builtin_datasets(sample_db) -> None:
    """加载内置数据集，保留完整的目录层级结构

    幂等设计：若数据集已存在且含样本则跳过，若数据集已存在但无样本则补录样本。
    流式读取：逐行读取 JSONL 文件，避免大文件导致 MemoryError。
    """
    for jsonl_file in sorted(_BASE.rglob("*.jsonl")):
        relative_path = jsonl_file.relative_to(_BASE)
        dataset_name = f"builtin_datasets/{relative_path.with_suffix('')}"
        risk_type = jsonl_file.parent.name

        dataset_id: int | None = None
        try:
            dataset_id = await sample_db.create_dataset(dataset_name, risk_type)
        except ValueError:
            existing = await sample_db.get_dataset_by_name(dataset_name)
            if existing is None:
                continue
            dataset_id = existing["dataset_id"]
            sample_count = await sample_db.get_sample_count_by_dataset(dataset_id)
            if sample_count > 0:
                continue

        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    s = json.loads(line)
                    await sample_db.add_sample(s["subtype"], s["poc"], dataset_id)
                except Exception:
                    pass
