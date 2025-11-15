from fastapi import FastAPI

from api.core.lifespan import lifespan
from api.routers.health import router as health_router
from api.routers.music import router as music_router
from api.routers.auth import router as auth_router


# ----------------------------------------------- #


def create_app() -> FastAPI:
    app = FastAPI(title="MSV2 Webapp API", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(music_router)
    app.include_router(auth_router)

    return app


# ----------------------------------------------- #

app = create_app()
