from fastapi import APIRouter
from fastapi.responses import FileResponse


health_router = APIRouter(tags=["health"], include_in_schema=False)


@health_router.get("/")
def root_endpoint():
    return {"message": "Welcome to the Diagnosticator API!"}


@health_router.get("/health")
async def get_health_check_endpoint():
    return {"status": "healthy", "message": "MSV2 Webapp API is running!"}


@health_router.get("/favicon.ico")
async def get_favicon_endpoint():
    return FileResponse("favicon.ico")
