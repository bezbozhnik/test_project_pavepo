from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import app_configs, settings
from src.routers.audio_route import audio_router
from src.routers.auth_route import auth_router
from src.routers.default_route import default_router
from src.routers.users_route import users_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(**app_configs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(default_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(audio_router)
