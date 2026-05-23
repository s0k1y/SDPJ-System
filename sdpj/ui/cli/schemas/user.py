"""用户命令输入验证 — 对齐 WebUI schemas/user.py"""

from pydantic import BaseModel


class AuthParams(BaseModel):
    username: str
    password: str


class AccountOpParams(BaseModel):
    operation: str
    params: dict = {}


class DACOpParams(BaseModel):
    operation: str
    params: dict
