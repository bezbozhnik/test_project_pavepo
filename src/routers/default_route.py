from time import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

default_router = APIRouter()


@default_router.get("/", response_class=JSONResponse)
async def get_timestamp() -> dict:
    return {"timestamp": time()}
