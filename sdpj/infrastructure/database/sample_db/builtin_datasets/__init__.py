"""内置数据集加载器"""
import json
from pathlib import Path

_BASE = Path(__file__).parent


async def load_builtin_datasets(sample_db) -> None:
    """加载内置数据集，保留完整的目录层级结构"""
    for jsonl_file in sorted(_BASE.rglob("*.jsonl")):
        # 计算相对于 builtin_datasets 的完整路径
        relative_path = jsonl_file.relative_to(_BASE)

        # 添加 builtin_datasets 前缀，保留完整层级
        # 例如：builtin_datasets/attack_poc/prompt_injection/hijacking/gentelbench_goal_hijacking
        dataset_name = f"builtin_datasets/{relative_path.with_suffix('')}"

        # 风险类型从路径中提取（例如：hijacking）
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

