"""Debug test: verify TestClient works with database."""
from fastapi.testclient import TestClient

# Simulate what the conftest fixture does
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from collections.abc import Generator
from fastapi import FastAPI
from app.database import Base, get_db
from app.models import MenuItem  # noqa: F401

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

print("Tables:", list(Base.metadata.tables.keys()))


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.routers.menu import router as menu_router

app = FastAPI()
app.include_router(menu_router, prefix="/api")
app.dependency_overrides[get_db] = _override_get_db

# Test
with TestClient(app) as c:
    resp = c.post("/api/menu/items", json={"title": "Test Item"})
    print("Status:", resp.status_code)
    print("Body:", resp.text[:200])

    resp2 = c.get("/api/menu/tree")
    print("Tree status:", resp2.status_code)
    print("Tree:", resp2.text[:200])
