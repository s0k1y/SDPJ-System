"""内置数据集加载器"""
import json
from pathlib import Path

_BASE = Path(__file__).parent


async def load_builtin_datasets(sample_db) -> None:
    for jsonl_file in sorted(_BASE.rglob("*.jsonl")):
        dataset_name = jsonl_file.stem
        risk_type = jsonl_file.parent.name
        try:
            dataset_id = await sample_db.create_dataset(dataset_name, risk_type)
        except ValueError:
            continue
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                s = json.loads(line)
                await sample_db.add_sample(s["subtype"], s["poc"], dataset_id)
            except Exception:
                pass
