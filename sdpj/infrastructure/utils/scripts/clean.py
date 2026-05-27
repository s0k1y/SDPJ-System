"""清理脚本 — 清理构建产物和缓存."""

import shutil
from pathlib import Path


def main() -> None:  # noqa: D103
    root = Path(__file__).resolve().parents[4]
    targets = [
        root / "dist",
        root / "build",
        root / ".pytest_cache",
        root / "htmlcov",
    ]
    for pattern in ("__pycache__", "*.egg-info"):
        targets.extend(root.rglob(pattern))

    removed = 0
    for target in targets:
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed += 1


if __name__ == "__main__":
    main()
