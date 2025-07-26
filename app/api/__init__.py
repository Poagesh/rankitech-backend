# app/api/__init__.py
"""API submodule for routes."""
from fastapi import APIRouter
from app.api.routes import router as api_router

router = APIRouter()
router.include_router(api_router, prefix="/api", tags=["api"])
