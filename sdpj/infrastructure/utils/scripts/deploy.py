"""部署脚本 — Docker Compose 部署"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    compose_file = root / "docker-compose.yml"
    if not compose_file.exists():
        print(f"docker-compose.yml not found at {compose_file}")
        sys.exit(1)
    subprocess.check_call(
        ["docker", "compose", "-f", str(compose_file), "up", "-d", "--build"],
        cwd=str(root),
    )
    print("Deployment completed.")


if __name__ == "__main__":
    main()
