from fastapi import APIRouter, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from api.core.dependencies import get_current_user, get_auth_repository
from api.models.auth import UserCreate, Token, User, UserInDB
from api.repositories.auth_repo import AuthRepository
from api.handlers.auth import (
    register_user_handler,
    login_handler,
    refresh_token_handler,
    logout_handler,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register_user_endpoint(
    user_create: UserCreate,
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    return await register_user_handler(user_create, auth_repo)


@router.post("/login", response_model=Token)
async def login_endpoint(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    return await login_handler(response, form_data, auth_repo)


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    return await refresh_token_handler(request, response, auth_repo)


@router.post("/logout")
async def logout_endpoint(
    response: Response,
    current_user: UserInDB = Depends(get_current_user),  # <--- Type hint changed to UserInDB
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    return await logout_handler(response, current_user, auth_repo)


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
