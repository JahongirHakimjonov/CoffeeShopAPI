from fastapi.routing import APIRouter

from api.api_v1 import auth, user

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(user.router)
