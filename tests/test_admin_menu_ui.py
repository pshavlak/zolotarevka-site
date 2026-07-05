"""Tests for admin menu UI — CRUD API integration with admin templates."""

import os

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

os.environ["SESSION_SECRET"] = "test-secret-test-secret"


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_client():
    """Return a TestClient with an authenticated admin session."""
    client = TestClient(app)
    r = client.post("/admin/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert r.status_code == 302
    # Set the cookies on the client
    for key, value in r.cookies.items():
        client.cookies.set(key, value)
    return client


class TestAdminMenuUI:

    def test_login_page_renders(self, client):
        """The login page should render as HTML."""
        client = TestClient(app)
        r = client.get("/admin/login")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert "login" in r.text.lower() or "вход" in r.text.lower()

    def test_admin_page_requires_auth(self, client):
        """Unauthenticated requests to /admin/ should redirect to login."""
        client = TestClient(app)
        r = client.get("/admin/", follow_redirects=False)
        assert r.status_code == 302
        assert "/admin/login" in r.headers.get("location", "")

    def test_admin_menu_page_requires_auth(self, client):
        """Unauthenticated requests to /admin/menu should redirect."""
        client = TestClient(app)
        r = client.get("/admin/menu", follow_redirects=False)
        assert r.status_code == 302
        assert "/admin/login" in r.headers.get("location", "")

    def test_admin_page_renders_authenticated(self, auth_client):
        """Authenticated GET /admin/ should render the menu management page."""
        r = auth_client.get("/admin/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        # Should include admin CSS and SortableJS
        assert "admin.css" in r.text
        assert "sortable" in r.text.lower()

    def test_admin_menu_page_renders(self, auth_client):
        """Authenticated GET /admin/menu should render the menu management page."""
        r = auth_client.get("/admin/menu")
        assert r.status_code == 200
        assert "admin.css" in r.text
        assert "admin-menu.js" in r.text

    def test_create_menu_item_via_api(self, auth_client):
        """Create a top-level menu item via API."""
        r = auth_client.post("/api/menu/items", json={"title": "Главная", "url": "/", "type": "page"})
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Главная"
        assert data["url"] == "/"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_nested_menu_item(self, auth_client):
        """Create a parent and child menu item."""
        parent = auth_client.post("/api/menu/items", json={"title": "Школа", "url": "/school", "type": "page"}).json()
        child = auth_client.post("/api/menu/items", json={
            "title": "Новости школы",
            "url": "/school/news",
            "type": "page",
            "parent_id": parent["id"],
        }).json()
        assert child["parent_id"] == parent["id"]

    def test_list_menu_items(self, auth_client):
        """List all menu items."""
        auth_client.post("/api/menu/items", json={"title": "Главная", "url": "/"})
        auth_client.post("/api/menu/items", json={"title": "Школа", "url": "/school"})
        r = auth_client.get("/api/menu/items")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_update_menu_item(self, auth_client):
        """Update a menu item's title."""
        item = auth_client.post("/api/menu/items", json={"title": "Old", "url": "/old"}).json()
        r = auth_client.put(f"/api/menu/items/{item['id']}", json={"title": "Новое название"})
        assert r.status_code == 200
        assert r.json()["title"] == "Новое название"

    def test_toggle_active(self, auth_client):
        """Toggle a menu item to inactive."""
        item = auth_client.post("/api/menu/items", json={"title": "Test", "url": "/test"}).json()
        r = auth_client.put(f"/api/menu/items/{item['id']}", json={"is_active": False})
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_delete_menu_item(self, auth_client):
        """Delete a menu item."""
        item = auth_client.post("/api/menu/items", json={"title": "Delete me", "url": "/delete-me"}).json()
        r = auth_client.delete(f"/api/menu/items/{item['id']}")
        assert r.status_code == 204
        r = auth_client.get("/api/menu/items")
        assert len(r.json()) == 0

    def test_delete_with_children_cascades(self, auth_client):
        """Deleting a parent should cascade delete children."""
        parent = auth_client.post("/api/menu/items", json={"title": "Parent", "url": "/parent"}).json()
        auth_client.post("/api/menu/items", json={
            "title": "Child", "url": "/child", "parent_id": parent["id"]
        })
        auth_client.delete(f"/api/menu/items/{parent['id']}")
        r = auth_client.get("/api/menu/items")
        assert len(r.json()) == 0

    def test_reorder_menu(self, auth_client):
        """Reorder two menu items."""
        item1 = auth_client.post("/api/menu/items", json={"title": "A", "url": "/a"}).json()
        item2 = auth_client.post("/api/menu/items", json={"title": "B", "url": "/b"}).json()
        r = auth_client.put("/api/menu/reorder", json=[
            {"id": item1["id"], "order": 2},
            {"id": item2["id"], "order": 1},
        ])
        assert r.status_code == 200

    def test_menu_tree(self, auth_client):
        """Get menu tree returns nested structure."""
        parent = auth_client.post("/api/menu/items", json={"title": "P", "url": "/p"}).json()
        auth_client.post("/api/menu/items", json={
            "title": "C", "url": "/c", "parent_id": parent["id"]
        })
        r = auth_client.get("/api/menu/tree")
        assert r.status_code == 200
        tree = r.json()
        assert len(tree) == 1
        assert tree[0]["children"]  # has children
        assert tree[0]["children"][0]["title"] == "C"

    def test_public_menu_active_only(self, auth_client):
        """Public /api/menu endpoint should only return active items."""
        auth_client.post("/api/menu/items", json={"title": "Active", "url": "/active"})
        inactive = auth_client.post("/api/menu/items", json={"title": "Inactive", "url": "/inactive"}).json()
        auth_client.put(f"/api/menu/items/{inactive['id']}", json={"is_active": False})
        r = auth_client.get("/api/menu")
        assert r.status_code == 200
        titles = [item["title"] for item in r.json()]
        assert "Active" in titles
        assert "Inactive" not in titles

    def test_get_nonexistent_menu_item(self, auth_client):
        """Getting a non-existent menu item returns 404."""
        r = auth_client.get("/api/menu/items/999")
        assert r.status_code == 404
