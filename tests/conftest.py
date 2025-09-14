import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import User, UserRole
from app.core.security import get_password_hash


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_client(test_db_session):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user_agent(test_db_session):
    """Create test user with AGENT role."""
    user = User(
        email="agent@test.com",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.AGENT
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_admin(test_db_session):
    """Create test user with ADMIN role."""
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.ADMIN
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def agent_token(test_client, test_user_agent):
    """Get JWT token for agent user."""
    response = await test_client.post(
        "/users/login",
        json={"email": "agent@test.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def admin_token(test_client, test_user_admin):
    """Get JWT token for admin user."""
    response = await test_client.post(
        "/users/login",
        json={"email": "admin@test.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers_agent(agent_token):
    """Authorization headers for agent user."""
    return {"Authorization": f"Bearer {agent_token}"}


@pytest.fixture
def auth_headers_admin(admin_token):
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}