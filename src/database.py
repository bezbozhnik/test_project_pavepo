from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    CursorResult,
    Delete,
    ForeignKey,
    Identity,
    Insert,
    Integer,
    MetaData,
    Select,
    String,
    Update,
)
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.orm import declarative_base, relationship

from src.config import settings
from src.constants import DB_NAMING_CONVENTION
from src.models.auth import User, UserCreate

DATABASE_URL = str(settings.DATABASE_ASYNC_URL)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    pool_recycle=settings.DATABASE_POOL_TTL,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
)
metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


class UserDB(Base):
    __tablename__ = 'users'

    id = Column(Integer, Identity(), primary_key=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    is_admin = Column(Boolean, server_default="false", nullable=False)

    audio_files = relationship("UserAudioFileDB", back_populates="user")


class UserAudioFileDB(Base):
    __tablename__ = 'user_audio_files'

    id = Column(Integer, Identity(), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    user = relationship("UserDB", back_populates="audio_files")


async def create_user(
    user_data: UserCreate,
    connection: AsyncConnection | None = None,
) -> User:

    if not user_data.username:
        user_data.username = user_data.email.split("@")[0]

    insert_query = (
        Insert(UserDB)
        .values(username=user_data.username, email=user_data.email)
        .returning(UserDB.id, UserDB.email)
    )

    if not connection:
        async with engine.connect() as new_connection:
            result = await fetch_one(insert_query, new_connection, commit_after=True)
            return User(id=result["id"], username=user_data.username, email=result["email"], is_admin=False)
    else:
        result = await fetch_one(insert_query, connection, commit_after=True)
        return User(id=result["id"], username=user_data.username, email=result["email"], is_admin=False)


async def get_user_by_email(email: str, connection: AsyncConnection) -> dict | None:
    query = Select(UserDB).where(UserDB.email == email)
    result = await fetch_one(query, connection)
    if result:
        return User(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            is_admin=result["is_admin"]
            )
    return None


async def get_user_by_id(user_id: int, connection: AsyncConnection) -> User | None:
    query = Select(UserDB).where(UserDB.id == user_id)
    result = await fetch_one(query, connection)
    if result:
        return User(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            is_admin=result["is_admin"]
            )
    return None


async def update_user_data(
    user_id: int,
    update_data: dict,
    connection: AsyncConnection,
) -> User | None:
    update_query = (
        Update(UserDB)
        .where(UserDB.id == user_id)
        .values(**update_data)
        .returning(UserDB.id, UserDB.username, UserDB.email, UserDB.is_admin)
    )
    result = await fetch_one(update_query, connection, commit_after=True)
    if result:
        return User(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            is_admin=result["is_admin"]
            )
    return None


async def get_user_audio_files(user_id: int, connection: AsyncConnection) -> list[dict]:
    query = Select(UserAudioFileDB).where(UserAudioFileDB.user_id == user_id)
    results = await fetch_all(query, connection)
    return [
        {"file_name": row["file_name"], "file_path": row["file_path"]}
        for row in results
    ]


async def create_audio_file_record(
    user_id: int,
    file_name: str,
    file_path: str,
    connection: AsyncConnection,
) -> None:
    insert_query = (
        Insert(UserAudioFileDB)
        .values(user_id=user_id, file_name=file_name, file_path=file_path)
    )
    await execute(insert_query, connection, commit_after=True)


async def delete_user_by_id(user_id: int, connection: AsyncConnection) -> None:
    query = Delete(UserDB).where(UserDB.id == user_id)
    await execute(query, connection, commit_after=True)


async def fetch_one(
    select_query: Select | Insert | Update,
    connection: AsyncConnection | None = None,
    commit_after: bool = False,
) -> dict[str, Any] | None:
    if not connection:
        async with engine.connect() as new_connection:
            cursor = await _execute_query(select_query, new_connection, commit_after)
            return cursor.first()._asdict() if cursor.rowcount > 0 else None

    cursor = await _execute_query(select_query, connection, commit_after)
    return cursor.first()._asdict() if cursor.rowcount > 0 else None


async def fetch_all(
    select_query: Select | Insert | Update,
    connection: AsyncConnection | None = None,
    commit_after: bool = False,
) -> list[dict[str, Any]]:
    if not connection:
        async with engine.connect() as new_connection:
            cursor = await _execute_query(select_query, new_connection, commit_after)
            return [r._asdict() for r in cursor.all()]

    cursor = await _execute_query(select_query, connection, commit_after)
    return [r._asdict() for r in cursor.all()]


async def execute(
    query: Insert | Update,
    connection: AsyncConnection = None,
    commit_after: bool = False,
) -> None:
    if not connection:
        async with engine.connect() as new_connection:
            await _execute_query(query, new_connection, commit_after)
            return

    await _execute_query(query, connection, commit_after)


async def _execute_query(
    query: Select | Insert | Update,
    connection: AsyncConnection,
    commit_after: bool = False,
) -> CursorResult:
    result = await connection.execute(query)
    if commit_after:
        await connection.commit()

    return result


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    connection = await engine.connect()
    try:
        yield connection
    finally:
        await connection.close()
