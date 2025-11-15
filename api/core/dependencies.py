from datetime import datetime, timezone
from typing import Annotated
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import asyncpg

from api.core.security import decode_jwt
from api.models.auth import TokenData, UserInDB
from api.repositories.auth_repo import AuthRepository
from api.repositories.music_repo import MusicRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get asyncpg pool from application state."""
    return request.app.state.db_pool


def get_auth_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> AuthRepository:
    """Get AuthRepository instance."""
    return AuthRepository(pool)


def get_music_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> MusicRepository:
    """Get MusicRepository instance."""
    return MusicRepository(pool)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> UserInDB:
    """Validate JWT token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_jwt(token)
        if payload is None:
            raise credentials_exception
        token_data = TokenData(**payload)
    except JWTError:
        raise credentials_exception

    if token_data.sub is None:
        raise credentials_exception

    user = await auth_repo.get_user_by_email(token_data.sub)
    if user is None:
        raise credentials_exception

    # Check JTI for token revocation
    token_jti = payload.get("jti")
    if user.jti is None and token_jti is not None:
        raise credentials_exception
    if user.jti is not None and token_jti != user.jti:
        raise credentials_exception

    # Check expiration
    if payload.get("exp") and datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise credentials_exception

    return user


# Type aliases for cleaner injection
AuthRepo = Annotated[AuthRepository, Depends(get_auth_repository)]
MusicRepo = Annotated[MusicRepository, Depends(get_music_repository)]
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
