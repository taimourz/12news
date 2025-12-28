from fastapi import APIRouter
from app.api.v1.endpoints import archive, cache

api_router = APIRouter()
api_router.include_router(archive.router)
api_router.include_router(cache.router)