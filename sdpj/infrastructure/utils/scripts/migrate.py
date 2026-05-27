"""数据库迁移脚本 — Alembic 命令便捷包装."""

import subprocess
import sys
from pathlib import Path


def main() -> None:  # noqa: D103
    root = Path(__file__).resolve().parents[4]
    args = sys.argv[1:] or ["upgrade", "head"]
    subprocess.check_call(  # noqa: S603
        [sys.executable, "-m", "alembic", *args],
        cwd=str(root),
    )


if __name__ == "__main__":
    main()
