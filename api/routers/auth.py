from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from api.core.dependencies import AuthRepo, CurrentUser
from api.handlers.auth import (
    login_handler,
    guest_login_handler,
    logout_handler,
    refresh_token_handler,
    register_user_handler,
)
from api.models.auth import Token, User, UserCreate
from api.models.responses import SuccessResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=SuccessResponse)
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


@auth_router.post("/guest", response_model=Token)
async def guest_login_endpoint(
    auth_repo: AuthRepo,
    response: Response,
):
    return await guest_login_handler(auth_repo, response)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    auth_repo: AuthRepo,
):
    return await refresh_token_handler(request, auth_repo, response)


@auth_router.post("/logout", response_model=SuccessResponse)
async def logout_endpoint(
    response: Response,
    current_user: CurrentUser,
    auth_repo: AuthRepo,
):
    return await logout_handler(current_user.id, auth_repo, response)


@auth_router.get("/me", response_model=User)
async def users_me_endpoint(current_user: CurrentUser):
    return current_user
