from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: str
    username: str | None = None


class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    username: str
    email: str | None = None
    is_admin: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ProtectedResponse(BaseModel):
    message: str
