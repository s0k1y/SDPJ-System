"""用户相关 Pydantic 模型"""

from typing import Optional

from pydantic import BaseModel


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str = ""
    user_id: Optional[int] = None


class AccountOperationRequest(BaseModel):
    operation: str
    params: dict = {}


class DACOperationRequest(BaseModel):
    operation: str
    params: dict
