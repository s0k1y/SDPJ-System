"""用户命令输入验证 — 对齐 WebUI schemas/user.py."""

from pydantic import BaseModel


class AuthParams(BaseModel):  # noqa: D101
    username: str
    password: str


class AccountOpParams(BaseModel):  # noqa: D101
    operation: str
    params: dict = {}


class DACOpParams(BaseModel):  # noqa: D101
    operation: str
    params: dict
