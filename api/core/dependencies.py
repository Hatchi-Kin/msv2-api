from datetime import datetime, timezone

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from api.connectors.postgres_connector import PostgresConnector
from api.core.security import decode_jwt
from api.models.auth import TokenData, UserInDB


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db_connector(request: Request) -> PostgresConnector:
    return request.app.state.db_connector


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_connector: PostgresConnector = Depends(get_db_connector),
) -> UserInDB:
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

    user = await db_connector.get_user_by_email(token_data.sub)
    if user is None:
        raise credentials_exception

    # Check JTI for access token revocation
    token_jti = payload.get("jti")
    if user.jti is None and token_jti is not None:
        # User has no active refresh token, but token has a JTI (e.g., after logout)
        raise credentials_exception
    if user.jti is not None and token_jti != user.jti:
        # User has an active refresh token, but it doesn't match the token's JTI
        raise credentials_exception

    # Check if access token is expired (already handled by decode_jwt, but good to be explicit)
    if payload.get("exp") and datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise credentials_exception

    return user
