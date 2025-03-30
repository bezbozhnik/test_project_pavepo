from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncConnection

from src.config import settings
from src.database import create_user, get_db_connection, get_user_by_email
from src.models.auth import ProtectedResponse, TokenResponse, User, UserCreate
from src.services.auth import create_access_token, decode_access_token

auth_router = APIRouter(prefix='/auth', tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    connection: AsyncConnection = Depends(get_db_connection),
) -> User:
    token_data = decode_access_token(token)
    email = token_data["email"]

    user = await get_user_by_email(email, connection)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@auth_router.get("/yandex/", response_model=dict)
async def auth_yandex() -> dict:
    auth_url = (f"{settings.YANDEX_AUTH_URL}?response_type=code&client_id={settings.YANDEX_CLIENT_ID}"
                f"&redirect_uri={settings.YANDEX_REDIRECT_URI}")
    return {"auth_url": auth_url}


@auth_router.get("/callback/", response_model=TokenResponse)
async def auth_callback(code: str, connection: AsyncConnection = Depends(get_db_connection)) -> TokenResponse:
    async with httpx.AsyncClient() as client:
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.YANDEX_CLIENT_ID,
            "client_secret": settings.YANDEX_CLIENT_SECRET,
            "redirect_uri": settings.YANDEX_REDIRECT_URI,
        }
        response = await client.post(settings.YANDEX_TOKEN_URL, data=token_data)

        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from Yandex"
            )

        access_token = response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token received")

        headers = {"Authorization": f"OAuth {access_token}"}
        user_info_response = await client.get("https://login.yandex.ru/info", headers=headers)

        if user_info_response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from Yandex")

        user_info = user_info_response.json()
        email = user_info.get("default_email")
        username = user_info.get("login")

        user = await get_user_by_email(email, connection)
        if not user:
            user = await create_user(UserCreate(email=email, username=username), connection=connection)

        internal_token = create_access_token(
            data={"sub": email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return TokenResponse(access_token=internal_token, token_type="bearer")


@auth_router.post("/token/refresh/", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)) -> TokenResponse:
    new_token = create_access_token(
        data={"sub": current_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return TokenResponse(access_token=new_token, token_type="bearer")


@auth_router.get("/protected/", response_model=ProtectedResponse)
async def read_protected_data(current_user: User = Depends(get_current_user)) -> ProtectedResponse:
    return ProtectedResponse(message=f"Hello, {current_user.username}")
