"""Test fixtures for menu CRUD tests."""

from collections.abc import Generator
import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, get_db
from app.models import MenuItem, Page  # noqa: F401 — register models with Base

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


def _make_test_app(router, prefix: str = "") -> FastAPI:
    """Create a test app that includes auth routes, session, and DB override."""
    from app.routers.auth import router as auth_router

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-test-secret")
    app.include_router(auth_router)
    app.include_router(router, prefix=prefix)
    app.dependency_overrides[get_db] = _override_get_db
    return app


def _authenticate(client: TestClient) -> None:
    """Authenticate the test client by posting to /admin/login."""
    r = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert r.status_code == 302, f"Auth failed: {r.status_code}"
    for key, value in r.cookies.items():
        client.cookies.set(key, value)


@pytest.fixture
def client(setup_db: None) -> Generator[TestClient, None, None]:
    """Provide an authenticated TestClient with menu router + isolated DB."""
    from app.routers.menu import router as menu_router

    app = _make_test_app(menu_router, prefix="/api")
    with TestClient(app) as c:
        _authenticate(c)
        yield c


@pytest.fixture
def anon_client(setup_db: None) -> Generator[TestClient, None, None]:
    """Provide an unauthenticated TestClient with menu router."""
    from app.routers.menu import router as menu_router

    app = _make_test_app(menu_router, prefix="/api")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def page_client(setup_db: None) -> Generator[TestClient, None, None]:
    """Provide an authenticated TestClient with page router + isolated DB."""
    from app.routers.page import router as page_router

    app = _make_test_app(page_router, prefix="/api")
    with TestClient(app) as c:
        _authenticate(c)
        yield c


@pytest.fixture
def anon_page_client(setup_db: None) -> Generator[TestClient, None, None]:
    """Provide an unauthenticated TestClient with page router."""
    from app.routers.page import router as page_router

    app = _make_test_app(page_router, prefix="/api")
    with TestClient(app) as c:
        yield c
