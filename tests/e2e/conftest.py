import os  # noqa: D100
import tempfile

_e2e_db_dir = tempfile.mkdtemp(prefix="sdpj_e2e_")
_e2e_db_path = os.path.join(_e2e_db_dir, "sdpj.db")  # noqa: PTH118
os.environ["SDPJ_DB_URL"] = f"sqlite+aiosqlite:///{_e2e_db_path}"

import asyncio

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient
from sdpj.ui.webui.backend.app import app
from sdpj.bootstrap import build_scheduler
from sdpj.ui.cli.main import CLIContext


@pytest.fixture(scope="session")
def client():  # noqa: ANN201, D103
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def _cli_scheduler():  # noqa: ANN202
    scheduler = build_scheduler(skip_builtin_datasets=True)
    asyncio.run(scheduler.startup(skip_builtin_datasets=True))
    return scheduler


@pytest.fixture(autouse=True)
def _patch_cli_bootstrap(monkeypatch, _cli_scheduler) -> None:  # noqa: ANN001
    import sdpj.ui.cli.main as cli_mod

    monkeypatch.setattr(cli_mod, "_bootstrap", lambda: _cli_scheduler)

    _original_make_context = cli_mod.cli.make_context

    def _patched_make_context(ctx_name, args, parent=None, **extra):  # noqa: ANN001, ANN003, ANN202
        ctx = _original_make_context(ctx_name, args, parent=parent, **extra)
        if isinstance(ctx.obj, cli_mod.CLIContext):
            ctx.obj._scheduler = _cli_scheduler
        return ctx

    monkeypatch.setattr(cli_mod.cli, "make_context", _patched_make_context)
