from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.validation import validate_password

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def _normalize_password_error(exc: Exception) -> None:
    if "72 bytes" in str(exc):
        raise ValueError(
            "This password is too long for a legacy account hash. Please reset your password."
        ) from exc
    raise exc


def hash_password(password: str) -> str:
    validate_password(password)
    try:
        return pwd_context.hash(password)
    except Exception as exc:
        _normalize_password_error(exc)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    validate_password(plain_password)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as exc:
        _normalize_password_error(exc)


def create_access_token(subject: str | int) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
