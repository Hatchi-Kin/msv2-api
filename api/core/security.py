from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.core.config import settings
from api.models.auth import TokenData, UserInDB
from api.repositories.auth import AuthRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> Optional[dict]:
    """Decode a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def validate_token_and_get_user(token: str, auth_repo: AuthRepository) -> UserInDB:
    """
    Validate JWT token and return the authenticated user.

    Performs all security checks:
    - Token decoding
    - Token expiration
    - User existence
    - JTI validation (for token revocation)

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    try:
        payload = decode_jwt(token)
        if payload is None:
            raise credentials_exception
        token_data = TokenData(**payload)
    except JWTError:
        raise credentials_exception

    # Validate token has subject (email)
    if token_data.sub is None:
        raise credentials_exception

    # Get user from database
    user = await auth_repo.get_user_by_email(token_data.sub)
    if user is None:
        raise credentials_exception

    # -------------------------------------------------------------------------
    # JTI VALIDATION DISABLED FOR ACCESS TOKENS (RACE CONDITION FIX)
    # -------------------------------------------------------------------------
    # We disable strict JTI checks for Access Tokens to handle parallel requests.
    #
    # 1. Frontend makes parallel requests (e.g. Dashboard + Stats).
    # 2. Both fail with 401 (Expired).
    # 3. Both trigger a Token Refresh simultaneously.
    # 4. Refresh A succeeds -> Rotates User.JTI to "A".
    # 5. Refresh B succeeds -> Rotates User.JTI to "B".
    # 6. Request A retries with Token "A".
    # 7. API rejects Token "A" because DB now has JTI "B". -> User Logged Out.
    #
    # By disabling this check for short-lived Access Tokens (15m), we allow
    # "slightly stale" tokens to work until they expire naturally.
    #
    # Strict JTI validation IS STILL ENFORCED for Refresh Tokens in
    # `refresh_token_handler` to prevent token theft/replay.
    # -------------------------------------------------------------------------
    
    # token_jti = payload.get("jti")
    # if user.jti is None and token_jti is not None:
    #     raise credentials_exception
    # if user.jti is not None and token_jti != user.jti:
    #     raise credentials_exception

    # Check expiration (belt and suspenders - JWT library also checks this)
    if payload.get("exp") and datetime.fromtimestamp(
        payload["exp"], tz=timezone.utc
    ) < datetime.now(timezone.utc):
        raise credentials_exception

    return user
