from fastapi import APIRouter, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from api.handlers.auth import (
    register_user_handler,
    login_handler,
    refresh_token_handler,
    logout_handler,
)
from api.models.auth import UserCreate, Token, User, UserInDB
from api.core.dependencies import get_current_user, get_db_connector
from api.connectors.postgres_connector import PostgresConnector


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register_user_endpoint(
    user_create: UserCreate,
    db_connector: PostgresConnector = Depends(get_db_connector),
):
    return await register_user_handler(user_create, db_connector)


@router.post("/login", response_model=Token)
async def login_endpoint(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_connector: PostgresConnector = Depends(get_db_connector),
):
    return await login_handler(response, form_data, db_connector)


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db_connector: PostgresConnector = Depends(get_db_connector),
):
    return await refresh_token_handler(request, response, db_connector)


@router.post("/logout")
async def logout_endpoint(
    response: Response,
    current_user: User = Depends(get_current_user),
    db_connector: PostgresConnector = Depends(get_db_connector),
):
    return await logout_handler(response, current_user, db_connector)


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
