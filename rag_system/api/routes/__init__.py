"""Routes module - exports all API routers."""

from .upload import router as upload_router
from .files import router as files_router
from .history import router as history_router
from .library import router as library_router

__all__ = ['upload_router', 'files_router', 'history_router', 'library_router']
