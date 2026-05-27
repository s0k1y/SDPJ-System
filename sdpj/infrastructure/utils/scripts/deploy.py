"""部署脚本 — Docker Compose 部署."""

import subprocess
import sys
from pathlib import Path


def main() -> None:  # noqa: D103
    root = Path(__file__).resolve().parents[4]
    compose_file = root / "docker-compose.yml"
    if not compose_file.exists():
        sys.exit(1)
    subprocess.check_call(  # noqa: S603
        ["docker", "compose", "-f", str(compose_file), "up", "-d", "--build"],  # noqa: S607
        cwd=str(root),
    )


if __name__ == "__main__":
    main()
