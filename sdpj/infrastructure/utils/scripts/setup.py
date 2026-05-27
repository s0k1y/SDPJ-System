"""安装脚本 — 初始化项目环境."""

import subprocess
import sys
from pathlib import Path


def main() -> None:  # noqa: D103
    root = Path(__file__).resolve().parents[4]
    req = root / "requirements.txt"
    if not req.exists():
        sys.exit(1)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])  # noqa: S603


if __name__ == "__main__":
    main()
