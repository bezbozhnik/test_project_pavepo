from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database import delete_user_by_id, get_db_connection, get_user_by_id, update_user_data
from src.models.auth import User, UserUpdate
from src.routers.auth_route import get_current_user

users_router = APIRouter(prefix='/users')


@users_router.get(
    "/{user_id}/",
    response_model=User,
    responses={
        status.HTTP_200_OK: {"model": User, "description": "User found"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_db_connection),
) -> User:

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this user",
        )

    db_user = await get_user_by_id(user_id, connection)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return db_user


@users_router.patch(
    "/{user_id}/",
    response_model=User,
    responses={
        status.HTTP_200_OK: {"model": User, "description": "User updated successfully"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_db_connection),
) -> User:

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this user",
        )

    updated_user = await update_user_data(user_id, update_data.model_dump(exclude_unset=True), connection)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@users_router.delete(
    "/{user_id}/",
    response_model=dict,
    responses={
        status.HTTP_200_OK: {"description": "User deleted successfully"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
    },
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_db_connection),
) -> dict:

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete users",
        )

    await delete_user_by_id(user_id, connection)

    return {"message": f"User with ID {user_id} has been deleted"}
