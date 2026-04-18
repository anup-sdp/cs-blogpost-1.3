from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # changes for async
from sqlalchemy.orm import DeclarativeBase
from config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url # "sqlite+aiosqlite:///./blog.db" (older, replaced with PostgreSQL in .env)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args={"check_same_thread": False}, # only valid for SQLite / aiosqlite, not needed for PostgreSQL
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
