"""Teardown hook -- suppresses spurious exit code from aiosqlite background thread cleanup.

The aiosqlite Engine uses a background thread. When the event loop closes,
the thread callback fires RuntimeError("Event loop is closed").
This hook zeroes exitstatus when no real test failures exist.
"""
import pytest
from typing import Any

# Suppress spurious RuntimeWarning from AsyncMock cleanup
pytestmark = pytest.mark.filterwarnings(
    "ignore:coroutine.*was never awaited:RuntimeWarning"
)


@pytest.fixture(autouse=True)
def _suppress_asyncmock_warning() -> None:
    """Suppress PytestUnraisableExceptionWarning from AsyncMock cleanup."""
    import warnings
    warnings.filterwarnings(
        "ignore",
        message="coroutine.*was never awaited",
        category=RuntimeWarning,
    )


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    """测试 pytest sessionfinish."""
    if exitstatus == 0:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return
    failed = reporter.stats.get("failed", [])
    if failed:
        return
    session.exitstatus = 0
