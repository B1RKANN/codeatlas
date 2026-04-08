from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import create_access_token
from app.core.validation import validate_password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        return validate_password(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    @classmethod
    def create_for_user(cls, user_id: int) -> "TokenResponse":
        return cls(access_token=create_access_token(user_id))
