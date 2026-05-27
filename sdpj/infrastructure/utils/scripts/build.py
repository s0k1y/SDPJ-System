"""构建脚本 — 打包项目."""

import subprocess
import sys
from pathlib import Path


def main() -> None:  # noqa: D103
    root = Path(__file__).resolve().parents[4]
    subprocess.check_call(  # noqa: S603
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(root / "dist")],
        cwd=str(root),
    )


if __name__ == "__main__":
    main()
