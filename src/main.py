import firebase_admin
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from firebase_admin import credentials
from starlette.staticfiles import StaticFiles

from src.auth.base_config import auth_backend, fastapi_users
from src.auth.schemas import UserRead, UserCreate
from src.ml.detectors.face_recognise.face_recognition import load_images

from src.ml.router import router as router_operation

from src.config import REDIS_HOST, REDIS_PORT


from src.notificattion.router import router as router_tasks

from redis import asyncio as aioredis


app = FastAPI(
    title="WorkspaceMonitor app"
)

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
load_images()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router_operation)
app.include_router(router_tasks)


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

