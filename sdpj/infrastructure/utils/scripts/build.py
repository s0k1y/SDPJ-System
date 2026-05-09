"""构建脚本 — 打包项目"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    subprocess.check_call(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(root / "dist")],
        cwd=str(root),
    )
    print("Build completed. Output in dist/")


if __name__ == "__main__":
    main()
