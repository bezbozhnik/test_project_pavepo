from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database import create_audio_file_record, get_db_connection, get_user_audio_files
from src.models.audio import UploadAudioFileResponse, UserAudioFilesResponse
from src.models.auth import User
from src.routers.auth_route import get_current_user
from src.utils.save import save_file

audio_router = APIRouter(prefix="/audio", tags=["Audio Files"])


@audio_router.get(
    "/user/{user_id}/",
    response_model=UserAudioFilesResponse,
    responses={
        status.HTTP_200_OK: {"model": UserAudioFilesResponse, "description": "User audio files found"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user_audio_files_route(
    user_id: int,
    current_user: User = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_db_connection),
) -> UserAudioFilesResponse:

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this user's audio files",
        )

    audio_files = await get_user_audio_files(user_id, connection)
    if not audio_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio files found for this user",
        )

    return UserAudioFilesResponse(user_id=user_id, files=audio_files)


@audio_router.post(
    "/upload/",
    response_model=UploadAudioFileResponse,
    responses={
        status.HTTP_201_CREATED: {"model": UploadAudioFileResponse, "description": "File uploaded successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid file or upload failed"},
    },
)
async def upload_audio_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_db_connection),
) -> UploadAudioFileResponse:

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was uploaded",
        )

    file_path = await save_file(current_user.id, file)

    await create_audio_file_record(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        connection=connection,
    )

    return UploadAudioFileResponse(
        file_name=file.filename,
        file_path=file_path,
    )
