from fastapi import APIRouter

from app.api.routes import admin, anime, auth, collections, favorites, me, public

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(anime.router, prefix="/anime", tags=["anime"])
api_router.include_router(collections.router, prefix="/me/collections", tags=["collections"])
api_router.include_router(favorites.router, prefix="/me/favorites", tags=["favorites"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
