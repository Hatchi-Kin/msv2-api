from datetime import timedelta, datetime, timezone
from uuid import uuid4
from fastapi import HTTPException, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from api.repositories.auth_repo import AuthRepository
from api.core.config import settings
from api.core.dependencies import get_current_user, get_auth_repository
from api.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_jwt,
)
from api.models.auth import UserCreate, Token, UserInDB, RefreshTokenPayload


async def register_user_handler(
    user_create: UserCreate,
    auth_repo: AuthRepository,
):
    existing_user = await auth_repo.get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_create.password)
    _user_in_db = await auth_repo.create_user(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
    )
    return {"message": "User registered successfully"}


async def login_handler(
    response: Response,
    form_data: OAuth2PasswordRequestForm,
    auth_repo: AuthRepository,
) -> Token:
    user = await auth_repo.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    jti_uuid = str(uuid4())
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=refresh_token_expires
    )

    await auth_repo.update_user_jti(user.id, jti_uuid, datetime.now(timezone.utc) + refresh_token_expires)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=int(refresh_token_expires.total_seconds()),
        max_age=int(refresh_token_expires.total_seconds()),
    )
    return Token(access_token=access_token, token_type="bearer")


async def refresh_token_handler(
    request: Request,
    response: Response,
    auth_repo: AuthRepository,
) -> Token:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    payload = decode_jwt(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        refresh_token_payload = RefreshTokenPayload(**payload)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    user = await auth_repo.get_user_by_email(refresh_token_payload.sub)
    if not user or user.jti != refresh_token_payload.jti or user.jti_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_jti_uuid = str(uuid4())
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email, "jti": new_jti_uuid},
        expires_delta=access_token_expires,
    )
    new_refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "jti": new_jti_uuid},
        expires_delta=new_refresh_token_expires,
    )

    await auth_repo.update_user_jti(
        user.id, new_jti_uuid, datetime.now(timezone.utc) + new_refresh_token_expires
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=int(new_refresh_token_expires.total_seconds()),
        max_age=int(new_refresh_token_expires.total_seconds()),
    )
    return Token(access_token=new_access_token, token_type="bearer")


async def logout_handler(
    response: Response,
    current_user: UserInDB,
    auth_repo: AuthRepository,
):
    await auth_repo.clear_user_jti(current_user.id)
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="lax")
    return {"message": "Logged out successfully"}
