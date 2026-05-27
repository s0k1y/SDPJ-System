"""健康检查脚本 — 验证系统各组件状态"""

import sys


def main() -> None:  # noqa: D103
    checks_passed = 0
    checks_total = 0

    checks_total += 1
    try:
        import sdpj  # noqa: F401

        checks_passed += 1
    except ImportError as e:
        pass

    checks_total += 1
    try:
        from sdpj.infrastructure.database.sample_db import SampleDB  # noqa: F401
        from sdpj.infrastructure.database.result_db import ResultDB  # noqa: F401
        from sdpj.infrastructure.database.user_db import UserDB  # noqa: F401

        checks_passed += 1
    except ImportError as e:
        pass

    checks_total += 1
    try:
        from sdpj.ui.webui.backend.app import app  # noqa: F401

        checks_passed += 1
    except ImportError as e:
        pass

    sys.exit(0 if checks_passed == checks_total else 1)


if __name__ == "__main__":
    main()
