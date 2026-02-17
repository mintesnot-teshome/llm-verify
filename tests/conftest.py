"""Shared test fixtures for the AI Benchmarker test suite."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database session for testing.

    Each test gets a fresh database with all tables created.
    The session is rolled back after each test for isolation.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def sample_model_configs() -> list[dict]:
    """Sample model configurations for testing."""
    return [
        {
            "model_name": "gpt-4o",
            "provider": "openai",
            "api_key": "test-key-openai",
            "api_base_url": "",
        },
        {
            "model_name": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "api_key": "test-key-anthropic",
            "api_base_url": "",
        },
        {
            "model_name": "suspect-model",
            "provider": "suspect",
            "api_key": "test-key-suspect",
            "api_base_url": "https://api.suspect.example.com/v1",
        },
    ]
