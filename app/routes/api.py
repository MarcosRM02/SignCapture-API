from fastapi import APIRouter

from app.routes.endpoints import health, inference

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(inference.router, prefix="/inference", tags=["inference"])

