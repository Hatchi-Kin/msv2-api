from fastapi import FastAPI

from api.core.config import settings
from api.core.cors import add_cors_middleware
from api.core.lifespan import lifespan
from api.routers.auth import auth_router
from api.routers.objects import objects_router
from api.routers.coordinates import coordinates_router
from api.routers.favorites import favorites_router
from api.routers.health import health_router
from api.routers.metadata import metadata_router
from api.routers.playlists import playlists_router

# ----------------------------------------------- #


def create_app() -> FastAPI:
    app = FastAPI(
        title="MSV2 Webapp API",
        lifespan=lifespan,
        swagger_ui_parameters={"defaultModelsExpandDepth": "0"},
    )

    add_cors_middleware(app)

    app.include_router(auth_router)
    app.include_router(metadata_router)
    app.include_router(favorites_router)
    app.include_router(playlists_router)
    app.include_router(objects_router)
    app.include_router(coordinates_router)
    app.include_router(health_router)

    return app


# ----------------------------------------------- #

app = create_app()
