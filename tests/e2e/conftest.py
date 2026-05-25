import os
import tempfile

_e2e_db_dir = tempfile.mkdtemp(prefix="sdpj_e2e_")
_e2e_db_path = os.path.join(_e2e_db_dir, "sdpj.db")
os.environ["SDPJ_DB_URL"] = f"sqlite+aiosqlite:///{_e2e_db_path}"

import asyncio

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient
from sdpj.ui.webui.backend.app import app
from sdpj.bootstrap import build_scheduler
from sdpj.ui.cli.main import CLIContext


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def _cli_scheduler():
    scheduler = build_scheduler(skip_builtin_datasets=True)
    asyncio.run(scheduler.startup(skip_builtin_datasets=True))
    return scheduler


@pytest.fixture(autouse=True)
def _patch_cli_bootstrap(monkeypatch, _cli_scheduler):
    import sdpj.ui.cli.main as cli_mod

    monkeypatch.setattr(cli_mod, "_bootstrap", lambda: _cli_scheduler)

    _original_make_context = cli_mod.cli.make_context

    def _patched_make_context(ctx_name, args, parent=None, **extra):
        extra.setdefault("obj", CLIContext(_cli_scheduler))
        return _original_make_context(ctx_name, args, parent=parent, **extra)

    monkeypatch.setattr(cli_mod.cli, "make_context", _patched_make_context)
