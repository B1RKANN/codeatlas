from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = create_user(db, payload)
    except ValueError as exc:
        status_code = status.HTTP_409_CONFLICT
        if "already exists" not in str(exc).lower():
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return TokenResponse.create_for_user(user.id)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
