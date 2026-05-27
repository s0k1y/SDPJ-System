"""一次性数据迁移:为现有 DetectionTask.metadata_json 补齐 attack_path 字段.

迁移规则:
    metadata_json["encoding_type"] is None  →  attack_path = "direct"
    metadata_json["encoding_type"] = "<enc>" →  attack_path = "indirect:multi-encoding:<enc>"

执行时机:仅在 add-multimodal-injection 变更归档前运行一次,后续 detector 写入
新任务时直接写入 attack_path 字段,不再依赖此脚本.

幂等性:跳过已有 attack_path 字段的任务记录.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "SDPJ-System" / "sdpj" / "infrastructure" / "database" / "sdpj.db"


def derive_attack_path(encoding_type: object) -> str:
    if encoding_type is None:
        return "direct"
    if isinstance(encoding_type, str) and encoding_type:
        return f"indirect:multi-encoding:{encoding_type}"
    return "direct"


def main() -> int:
    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.text_factory = str
    try:
        cur = conn.cursor()
        cur.execute("SELECT task_id, metadata_json FROM DetectionTask")
        rows = cur.fetchall()
        updated = 0
        skipped = 0
        for task_id, metadata_raw in rows:
            try:
                meta = json.loads(metadata_raw) if metadata_raw else {}
            except json.JSONDecodeError:
                meta = {}
            if not isinstance(meta, dict):
                meta = {}
            if "attack_path" in meta and meta["attack_path"]:
                skipped += 1
                continue
            attack_path = derive_attack_path(meta.get("encoding_type"))
            meta["attack_path"] = attack_path
            cur.execute(
                "UPDATE DetectionTask SET metadata_json = ? WHERE task_id = ?",
                (json.dumps(meta, ensure_ascii=False), task_id),
            )
            updated += 1
        conn.commit()
        print(f"[OK] 迁移完成: updated={updated} skipped={skipped} total={len(rows)}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
