# tests/conftest.py
# pytest recognizes conftest automatically.

"""
This file configures pytest fixtures for integration testing our FastAPI blog project with 
a temporary test database and mocked AWS S3, and a test HTTP client that talks to our app without starting a real server.
Uses moto to mock AWS services in-memory,
"""
# uv run pytest tests/conftest.py -v
# uv run pytest -v

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
"""
^ psycopg (v3) async mode is incompatible with the default ProactorEventLoop that asyncio uses on Windows. You need to force the older SelectorEventLoop
"""


import os
from collections.abc import AsyncGenerator

# psycopg instead of asyncpg, SQLAlchemy 2.0 async testing best practices strongly recommend using psycopg (although asyncpg used in main app)
os.environ["DATABASE_URL"] = ("postgresql+psycopg://bloguser:blogpass@localhost/test_blog")
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

os.environ["S3_ACCESS_KEY_ID"] = "testing"
os.environ["S3_SECRET_ACCESS_KEY"] = "testing"
os.environ["S3_REGION"] = "us-east-1"

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

os.environ.pop("S3_ENDPOINT_URL", None)
os.environ.pop("AWS_ENDPOINT_URL_S3", None)
os.environ.pop("MINIO_ENDPOINT", None)

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from database import Base, get_db
from main import app

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session") # scope="session" means this fixture will be created once per test session, and shared across all tests
def test_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool,) # psycopg 3 driver in asynchronous mode ---
    return engine


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def db_session(
    test_engine,
    setup_database,
) -> AsyncGenerator[AsyncSession]:
    conn = await test_engine.connect()
    trans = await conn.begin()

    test_async_session = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()


@pytest.fixture
def mocked_aws():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=os.environ["S3_BUCKET_NAME"])
        yield s3


@pytest.fixture
async def client(
    db_session: AsyncSession,
    mocked_aws,
) -> AsyncGenerator[AsyncClient]:

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


async def create_test_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:
    response = await client.post(
        "/api/users",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> str:
    response = await client.post(
        "/api/users/token",
        data={ # data instead of json, because the token endpoint expects form data (application/x-www-form-urlencoded) ---
            "username": email, # ---
            "password": password,
        },
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


"""
pytest: 
pytest is a popular, full-featured testing framework for Python.
It's currently the most widely used testing tool in the Python ecosystem (even more popular than the built-in unittest module).
Key Features:
Plain assert, Fixtures (very powerful), Parametrized tests,
pytest will automatically find and run all tests that:
Are in files named test_*.py or *_test.py
Have functions starting with test_

Plugins (some popular ones): 
pytest-cov → code coverage, pytest-django → Django testing, pytest-asyncio → async tests, pytest-xdist → run tests in parallel, pytest-mock → mocking

Fixtures:
Fixtures are functions that run before each test function to set up resources 
(like database connections, temporary files, or mock data). They are highly modular and reusable.
"""

"""
psycopg : supports both synchronous and asynchronous usage. When used asynchronously, 
it provides an async interface while remaining compatible with the traditional DB-API 2.0 style. (this file uses TestClient, which is synchronous)
asyncpg : A high-performance, pure async PostgreSQL driver written specifically for asyncio. (often claimed to be ~3-5x faster than psycopg in raw benchmarks)
httpx : Async HTTP client for testing FastAPI endpoints
"""

"""
create bloguser with password blogpass in PostgreSQL:
Open pgAdmin 4
Expand Servers
Click your PostgreSQL server (usually “PostgreSQL 15/16”)
Enter your master password if prompted

Right-click Login/Group Roles
Click Create → Login/Group Role
In General tab:
Name: bloguser
Go to Definition tab:
Password: blogpass
Go to Privileges tab:
Enable Can login
Click Save

Sometimes ownership is enough, but to be safe:
Right-click test_blog
Go to Properties → Security
Ensure bloguser has full privileges
"""