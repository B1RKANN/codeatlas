from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.validation import validate_password


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        return validate_password(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime
