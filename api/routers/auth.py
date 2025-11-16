from fastapi import APIRouter, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from api.core.dependencies import AuthRepo, CurrentUser
from api.models.auth import UserCreate, Token, User
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
    auth_repo: AuthRepo,
):
    return await register_user_handler(user_create, auth_repo)


@router.post("/login", response_model=Token)
async def login_endpoint(
    auth_repo: AuthRepo,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    return await login_handler(response, form_data, auth_repo)


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    auth_repo: AuthRepo,
):
    return await refresh_token_handler(request, response, auth_repo)


@router.post("/logout")
async def logout_endpoint(
    auth_repo: AuthRepo,
    response: Response,
    current_user: CurrentUser,
):
    return await logout_handler(response, current_user, auth_repo)


@router.get("/me", response_model=User)
async def read_users_me(current_user: CurrentUser):
    return current_user
