from pathlib import Path

import aiofiles
from fastapi import UploadFile

MEDIA_DIR = Path("media/audio")


async def save_file(user_id: int, file: UploadFile) -> str:

    user_dir = MEDIA_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_dir / file.filename

    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)

    return str(file_path)
