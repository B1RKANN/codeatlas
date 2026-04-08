from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    @classmethod
    def create_for_user(cls, user_id: int) -> "TokenResponse":
        return cls(access_token=create_access_token(user_id))
