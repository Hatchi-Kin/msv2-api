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

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register")
async def register_user_endpoint(
    user_create: UserCreate,
    auth_repo: AuthRepo,
):
    return await register_user_handler(user_create, auth_repo)


@auth_router.post("/login", response_model=Token)
async def login_endpoint(
    auth_repo: AuthRepo,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    return await login_handler(form_data, auth_repo, response)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    auth_repo: AuthRepo,
):
    return await refresh_token_handler(request, auth_repo, response)


@auth_router.post("/logout")
async def logout_endpoint(
    response: Response,
    current_user: CurrentUser,
    auth_repo: AuthRepo,
):
    return await logout_handler(current_user, auth_repo, response)


@auth_router.get("/me", response_model=User)
async def users_me_endpoint(current_user: CurrentUser):
    return current_user
