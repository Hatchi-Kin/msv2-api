from fastapi import FastAPI

from api.core.lifespan import lifespan
from api.core.cors import add_cors_middleware
from api.routers.health import health_router
from api.routers.music_db import music_db_router
from api.routers.auth import auth_router
from api.routers.music_storage import music_storage_router


# ----------------------------------------------- #


def create_app() -> FastAPI:
    app = FastAPI(title="MSV2 Webapp API", lifespan=lifespan)

    add_cors_middleware(app)

    app.include_router(auth_router)
    app.include_router(music_db_router)
    app.include_router(music_storage_router)
    app.include_router(health_router)

    return app


# ----------------------------------------------- #

app = create_app()
