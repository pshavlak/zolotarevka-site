"""Test fixtures for menu CRUD tests."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.models import MenuItem  # noqa: F401 — register model with Base

import os
import tempfile

# Use a temp file so TestClient's thread sees the same database
# (in-memory SQLite is per-connection, so each TestClient request
# would get a separate blank DB without this).
_db_file = os.path.join(tempfile.gettempdir(), "zolotarevka_test.db")
# Ensure a clean start by removing any leftover from a prior run.
if os.path.exists(_db_file):
    os.remove(_db_file)

TEST_DATABASE_URL = f"sqlite:///{_db_file}"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db() -> Generator[None, None, None]:
    """Create tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_db: None) -> Generator[Session, None, None]:
    """Provide a clean database session per test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── FastAPI test client ────────────────────────────────────────────────────


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(setup_db: None) -> Generator[TestClient, None, None]:
    """Provide a sync TestClient with an isolated file-based database."""
    from app.routers.menu import router as menu_router

    app = FastAPI()
    app.include_router(menu_router, prefix="/api")
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c
