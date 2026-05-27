"""用户相关 Pydantic 模型."""


from pydantic import BaseModel


class AuthRequest(BaseModel):  # noqa: D101
    username: str
    password: str


class AuthResponse(BaseModel):  # noqa: D101
    success: bool
    message: str = ""
    user_id: int | None = None


class AccountOperationRequest(BaseModel):  # noqa: D101
    operation: str
    params: dict = {}


class DACOperationRequest(BaseModel):  # noqa: D101
    operation: str
    params: dict
