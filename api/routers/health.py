from fastapi import APIRouter

router = APIRouter(tags=["health"], include_in_schema=False)


@router.get("/")
def read_root():
    return {"message": "Welcome to the Diagnosticator API!"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "MSV2 Webapp API is running!"}
