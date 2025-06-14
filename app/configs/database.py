from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import Settings


class DatabaseConnection:
    def __init__(self, settings: Settings):
        self.async_engine = create_async_engine(
            settings.database.db_uri,
            echo=False,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
        )
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as err:
                await session.rollback()
                raise err
