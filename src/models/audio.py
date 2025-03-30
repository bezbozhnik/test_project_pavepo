from pydantic import BaseModel


class AudioFileInfo(BaseModel):
    file_name: str
    file_path: str


class UserAudioFilesResponse(BaseModel):
    user_id: int
    files: list[AudioFileInfo]


class UploadAudioFileResponse(BaseModel):
    file_name: str
    file_path: str
