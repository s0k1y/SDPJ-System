"""用户私有数据集加载器"""
import json
from pathlib import Path

_BASE = Path(__file__).parent


async def load_user_datasets(sample_db, user_id: int) -> None:
    """加载用户私有数据集，保留完整的目录层级结构

    Args:
        sample_db: 数据库实例
        user_id: 用户ID，用于隔离不同用户的数据集
    """
    user_dir = _BASE / str(user_id)
    if not user_dir.exists():
        return

    for jsonl_file in sorted(user_dir.rglob("*.jsonl")):
        # 计算相对于用户目录的完整路径
        relative_path = jsonl_file.relative_to(user_dir)

        # 添加 user_datasets 前缀，保留完整层级
        # 例如：user_datasets/{user_id}/custom_attack/my_dataset
        dataset_name = f"user_datasets/{user_id}/{relative_path.with_suffix('')}"

        # 风险类型从路径中提取
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
