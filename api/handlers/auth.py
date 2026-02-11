from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from api.core.config import settings
from api.core.exceptions import (
    AlreadyExistsException,
    InactiveUserException,
    UnauthorizedException,
)
from api.core.logger import logger
from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_password_hash,
    verify_password,
)
from api.models.auth import RefreshTokenPayload, Token, UserCreate
from api.models.responses import SuccessResponse
from api.repositories.auth import AuthRepository


async def register_user_handler(
    user_create: UserCreate,
    auth_repo: AuthRepository,
) -> SuccessResponse:
    existing_user = await auth_repo.get_user_by_email(user_create.email)
    if existing_user:
        raise AlreadyExistsException("Email")

    hashed_password = get_password_hash(user_create.password)
    await auth_repo.create_user(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
    )
    logger.info(f"New user registered: {user_create.email}")
    return SuccessResponse(message="User registered successfully")


async def login_handler(
    form_data: OAuth2PasswordRequestForm,
    auth_repo: AuthRepository,
    response: Response,
) -> Token:
    user = await auth_repo.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise UnauthorizedException("Incorrect email or password")
    if not user.is_active:
        raise InactiveUserException()

    jti_uuid = str(uuid4())
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=refresh_token_expires
    )

    await auth_repo.update_user_jti(
        user.id, jti_uuid, datetime.now(timezone.utc) + refresh_token_expires
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        expires=int(refresh_token_expires.total_seconds()),
        max_age=int(refresh_token_expires.total_seconds()),
    )
    return Token(access_token=access_token, token_type="bearer")


async def guest_login_handler(
    auth_repo: AuthRepository,
    response: Response,
) -> Token:
    # 1. Create a random guest user
    # generated email: guest_<random_string>@demo.msv2
    # generated password: <random_16_char_string>
    random_suffix = uuid4().hex[:8]
    guest_email = f"guest_{random_suffix}@demo.msv2"
    guest_password = token_urlsafe(16)

    hashed_password = get_password_hash(guest_password)

    # Create the user in DB
    user = await auth_repo.create_user(
        email=guest_email,
        username=f"Guest {random_suffix}",
        hashed_password=hashed_password,
    )
    logger.info(f"Created guest user: {guest_email}")

    # 2. Perform Login (Generation of Tokens)
    # This logic mimics login_handler exactly
    if not user.is_active:
        raise InactiveUserException()  # Should not happen for new users, but safety first

    jti_uuid = str(uuid4())
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "jti": jti_uuid}, expires_delta=refresh_token_expires
    )

    await auth_repo.update_user_jti(
        user.id, jti_uuid, datetime.now(timezone.utc) + refresh_token_expires
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        expires=int(refresh_token_expires.total_seconds()),
        max_age=int(refresh_token_expires.total_seconds()),
    )
    return Token(access_token=access_token, token_type="bearer")


async def refresh_token_handler(
    request: Request,
    auth_repo: AuthRepository,
    response: Response,
) -> Token:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing")

    payload = decode_jwt(refresh_token)
    if not payload:
        raise UnauthorizedException("Invalid refresh token")

    try:
        refresh_token_payload = RefreshTokenPayload(**payload)
    except Exception:
        raise UnauthorizedException("Invalid refresh token payload")

    user = await auth_repo.get_user_by_email(refresh_token_payload.sub)
    if (
        not user
        or user.jti != refresh_token_payload.jti
        or user.jti_expires_at < datetime.now(timezone.utc)
    ):
        logger.warning(
            f"Invalid refresh token attempt for: {refresh_token_payload.sub}"
        )
        raise UnauthorizedException("Invalid or expired refresh token")

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
        samesite="none",
        expires=int(new_refresh_token_expires.total_seconds()),
        max_age=int(new_refresh_token_expires.total_seconds()),
    )
    return Token(access_token=new_access_token, token_type="bearer")


async def logout_handler(
    current_user: int,
    auth_repo: AuthRepository,
    response: Response,
) -> SuccessResponse:
    await auth_repo.clear_user_jti(current_user)
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="none"
    )
    logger.info(f"User logged out: {current_user}")
    return SuccessResponse(message="Logged out successfully")
