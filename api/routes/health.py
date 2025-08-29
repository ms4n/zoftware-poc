from fastapi import APIRouter

# Create router
router = APIRouter(tags=["health"])


@router.get("/")
def read_root():
    return {"message": "Zoftware POC API", "status": "running"}


@router.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
