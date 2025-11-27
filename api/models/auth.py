from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    jti: Optional[str] = None
    jti_expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    id: int
    is_active: bool = True
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None


class RefreshTokenPayload(BaseModel):
    sub: str  # User email
    jti: str  # JWT ID
    exp: datetime  # Expiration time
