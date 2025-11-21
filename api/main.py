from fastapi import FastAPI

from api.core.config import settings
from api.core.cors import add_cors_middleware
from api.core.lifespan import lifespan
from api.routers.auth import auth_router
from api.routers.coordinates import coordinates_router
from api.routers.favorites import favorites_router
from api.routers.health import health_router
from api.routers.library import library_router
from api.routers.media import media_router
from api.routers.playlists import playlists_router

# ----------------------------------------------- #


def create_app() -> FastAPI:
    app = FastAPI(
        title="MSV2 Webapp API",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        swagger_ui_parameters={"defaultModelsExpandDepth": "0"},
    )

    add_cors_middleware(app)

    app.include_router(auth_router)
    app.include_router(library_router)
    app.include_router(favorites_router)
    app.include_router(playlists_router)
    app.include_router(media_router)
    app.include_router(coordinates_router)
    app.include_router(health_router)

    return app


# ----------------------------------------------- #

app = create_app()
