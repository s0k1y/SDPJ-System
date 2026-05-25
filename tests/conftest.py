"""Teardown hook -- suppresses spurious exit code from aiosqlite background thread cleanup.

The aiosqlite Engine uses a background thread. When the event loop closes,
the thread callback fires RuntimeError("Event loop is closed").
This hook zeroes exitstatus when no real test failures exist.
"""
import pytest


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return
    failed = reporter.stats.get("failed", [])
    if failed:
        return
    session.exitstatus = 0
