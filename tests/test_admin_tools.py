"""Tests for media, settings, and suggestions endpoints."""

import io
import json
import os

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal
from app.main import app

os.environ["SESSION_SECRET"] = "test-secret-test-secret"


@pytest.fixture(autouse=True)
def _db():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# ── Media Tests ───────────────────────────────────────────────────────────


class TestMedia:
    def test_list_empty(self, client):
        r = client.get("/api/media")
        assert r.status_code == 200
        assert r.json() == []

    def test_upload_and_list(self, client):
        # Upload
        file_bytes = b"fake-image-data"
        r = client.post(
            "/api/media/upload",
            files={"file": ("test.png", io.BytesIO(file_bytes), "image/png")},
            data={"alt_text": "Test image"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["original_name"] == "test.png"
        assert data["mime_type"] == "image/png"
        assert data["size_bytes"] == len(file_bytes)
        assert data["alt_text"] == "Test image"
        media_id = data["id"]

        # List
        r = client.get("/api/media")
        assert r.status_code == 200
        assert len(r.json()) == 1

        # Get by id
        r = client.get(f"/api/media/{media_id}")
        assert r.status_code == 200
        assert r.json()["id"] == media_id

    def test_get_nonexistent_media(self, client):
        r = client.get("/api/media/999")
        assert r.status_code == 404

    def test_update_media_alt_text(self, client):
        file_bytes = b"data"
        r = client.post(
            "/api/media/upload",
            files={"file": ("img.jpg", io.BytesIO(file_bytes), "image/jpeg")},
        )
        media_id = r.json()["id"]

        r = client.put(f"/api/media/{media_id}", json={"alt_text": "Updated alt"})
        assert r.status_code == 200
        assert r.json()["alt_text"] == "Updated alt"

    def test_delete_media(self, client):
        file_bytes = b"data"
        r = client.post(
            "/api/media/upload",
            files={"file": ("delete-me.txt", io.BytesIO(file_bytes), "text/plain")},
        )
        media_id = r.json()["id"]

        r = client.delete(f"/api/media/{media_id}")
        assert r.status_code == 204

        r = client.get("/api/media")
        assert r.json() == []

    def test_delete_nonexistent(self, client):
        r = client.delete("/api/media/999")
        assert r.status_code == 404


# ── Settings Tests ────────────────────────────────────────────────────────


class TestSettings:
    def test_list_empty(self, client):
        r = client.get("/api/settings")
        assert r.status_code == 200
        assert r.json() == []

    def test_upsert_and_read(self, client):
        r = client.put("/api/settings/site_name", json={"value": "Золотаревка"})
        assert r.status_code == 200
        assert r.json()["key"] == "site_name"
        assert r.json()["value"] == "Золотаревка"

        r = client.get("/api/settings/site_name")
        assert r.status_code == 200
        assert r.json()["value"] == "Золотаревка"

    def test_upsert_update_existing(self, client):
        client.put("/api/settings/theme", json={"value": "light"})
        r = client.put("/api/settings/theme", json={"value": "dark"})
        assert r.status_code == 200
        assert r.json()["value"] == "dark"

    def test_get_nonexistent(self, client):
        r = client.get("/api/settings/nonexistent")
        assert r.status_code == 404

    def test_list_multiple(self, client):
        client.put("/api/settings/a", json={"value": "1"})
        client.put("/api/settings/b", json={"value": "2"})
        client.put("/api/settings/c", json={"value": "3"})
        r = client.get("/api/settings")
        assert len(r.json()) == 3


# ── Suggestions Tests ─────────────────────────────────────────────────────


class TestSuggestions:
    def test_list_empty(self, client):
        r = client.get("/api/suggest")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_and_list(self, client):
        r = client.post(
            "/api/suggest",
            json={"content": "Great site!", "author_name": "Иван"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["content"] == "Great site!"
        assert data["author_name"] == "Иван"
        assert data["is_read"] is False

        r = client.get("/api/suggest")
        assert len(r.json()) == 1

    def test_create_with_contact(self, client):
        r = client.post(
            "/api/suggest",
            json={
                "content": "Add more photos",
                "author_name": "Петр",
                "author_contact": "petr@example.com",
            },
        )
        assert r.status_code == 201
        assert r.json()["author_contact"] == "petr@example.com"

    def test_mark_read(self, client):
        r = client.post("/api/suggest", json={"content": "Test"})
        sug_id = r.json()["id"]

        r = client.put(f"/api/suggest/{sug_id}/read")
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    def test_mark_read_nonexistent(self, client):
        r = client.put("/api/suggest/999/read")
        assert r.status_code == 404
