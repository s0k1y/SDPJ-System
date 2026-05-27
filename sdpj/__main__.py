"""SDPJ-System CLI 入口点 — python -m sdpj  /  sdpj."""

import logging
import sys
import threading

import click

from sdpj.ui.cli.main import cli

logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)


_original_thread_excepthook = threading.excepthook


def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
    """抑制 aiosqlite 后台线程在事件循环关闭后的竞态 Traceback..

    asyncio.run() 返回时关闭 loop,但 SQLAlchemy 持有的 aiosqlite
    连接后台线程可能还在往已关闭的 loop 投递回调,触发 RuntimeError.
    此竞态不影响业务正确性,只输出一行提示而非满屏 Traceback.
    """
    if (
        args.exc_type is RuntimeError
        and args.thread is not None
        and "_connection_worker_thread" in str(args.thread)
    ):
        return  # aiosqlite 竞态,静默忽略,避免解释器关闭时 stderr 死锁
    _original_thread_excepthook(args)


def main():  # noqa: ANN201
    """CLI 入口,正确传递 Click 退出码给 shell.  # noqa: D200, D205    ``sdpj`` 不带参数时显示帮助并退出码 0(而非报错).., E501
    """
    try:
        return cli(standalone_mode=False)
    except click.exceptions.NoArgsIsHelpError as e:
        e.show()
        return 0
    except click.exceptions.UsageError as e:
        e.show()
        return e.exit_code
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except SystemExit as e:
        return e.code if e.code is not None else 0


threading.excepthook = _thread_excepthook

if __name__ == "__main__":
    sys.exit(main())
