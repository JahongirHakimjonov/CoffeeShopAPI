from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import create_app
from core.settings import get_settings
from db.dependencies import get_db_session
from db.meta import meta
from db.models import load_all_models


@pytest.fixture(scope="session")
async def _engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create engine and databases.

    :yield: new engine.
    """
    settings = get_settings()

    load_all_models()

    engine = create_async_engine(str(settings.postgres_url))
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def dbsession(
        _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to a database.

    Fixture that returns SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.

    :param _engine: Current engine.
    :yields: async session.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest.fixture
async def fastapi_app(
        dbsession: AsyncSession,
) -> FastAPI:
    """
    fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: dbsession
    return application  # noqa: WPS331


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture
async def client(
        fastapi_app: FastAPI,
        anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """
    fixture that creates a client for requesting server.

    :param fastapi_app: the application.
    :param anyio_backend: backend for anyio pytest plugin.
    :yield: client for the app.
    """
    transport = ASGITransport(fastapi_app)
    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_celery_tasks(monkeypatch):
    monkeypatch.setattr("core.celery.tasks.confirm.send_confirm_task.delay", lambda *a, **kw: None)


@pytest.fixture
async def fake_jwt_token(client: AsyncClient) -> str:
    """
    A fixture that provides a fake JWT token for authentication.
    """
    email = "user@mail.com"
    password = "secret123"  # noqa:S105
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "first_name": "string",
            "last_name": "string",
            "password": password,
            "password_confirm": password,
        },
    )
    await client.post(
        "/api/v1/auth/verify",
        json={
            "email": email,
            "code": "1111",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    data = response.json()
    return data["access_token"]
