"""健康检查脚本 — 验证系统各组件状态"""

import sys


def main() -> None:
    checks_passed = 0
    checks_total = 0

    checks_total += 1
    try:
        import sdpj  # noqa: F401

        checks_passed += 1
        print("[OK] sdpj package importable")
    except ImportError as e:
        print(f"[FAIL] sdpj package import: {e}")

    checks_total += 1
    try:
        from sdpj.infrastructure.database.sample_db import SampleDB  # noqa: F401
        from sdpj.infrastructure.database.result_db import ResultDB  # noqa: F401
        from sdpj.infrastructure.database.user_db import UserDB  # noqa: F401

        checks_passed += 1
        print("[OK] Database modules importable")
    except ImportError as e:
        print(f"[FAIL] Database modules: {e}")

    checks_total += 1
    try:
        from sdpj.ui.webui.backend.app import app  # noqa: F401

        checks_passed += 1
        print("[OK] WebUI backend importable")
    except ImportError as e:
        print(f"[FAIL] WebUI backend: {e}")

    print(f"\n{checks_passed}/{checks_total} checks passed.")
    sys.exit(0 if checks_passed == checks_total else 1)


if __name__ == "__main__":
    main()
