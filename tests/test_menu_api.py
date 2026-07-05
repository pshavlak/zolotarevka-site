"""Integration tests for the menu FastAPI endpoints via TestClient."""

import pytest
from httpx import AsyncClient


class TestCreate:
    async def test_create_root_item(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/menu/items", json={"title": "Главная"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Главная"
        assert data["url"] == ""
        assert data["parent_id"] is None
        assert data["is_active"] is True
        assert data["order"] == 0
        assert data["type"] == "page"
        assert "id" in data

    async def test_create_child_item(self, async_client: AsyncClient) -> None:
        parent_resp = await async_client.post(
            "/api/menu/items", json={"title": "Родитель"}
        )
        parent_id = parent_resp.json()["id"]

        child_resp = await async_client.post(
            "/api/menu/items",
            json={"title": "Ребёнок", "parent_id": parent_id},
        )
        assert child_resp.status_code == 201
        assert child_resp.json()["parent_id"] == parent_id

    async def test_create_invalid_empty_title(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/menu/items", json={"title": ""})
        assert resp.status_code == 422

    async def test_create_missing_title(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/menu/items", json={})
        assert resp.status_code == 422


class TestRead:
    async def test_get_item_by_id(self, async_client: AsyncClient) -> None:
        created = await async_client.post(
            "/api/menu/items", json={"title": "Найти"}
        )
        item_id = created.json()["id"]

        resp = await async_client.get(f"/api/menu/items/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Найти"

    async def test_get_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/api/menu/items/9999")
        assert resp.status_code == 404

    async def test_list_items(self, async_client: AsyncClient) -> None:
        await async_client.post("/api/menu/items", json={"title": "A"})
        await async_client.post("/api/menu/items", json={"title": "B"})

        resp = await async_client.get("/api/menu/items")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestUpdate:
    async def test_update_title(self, async_client: AsyncClient) -> None:
        created = await async_client.post(
            "/api/menu/items", json={"title": "Старое"}
        )
        item_id = created.json()["id"]

        resp = await async_client.put(
            f"/api/menu/items/{item_id}",
            json={"title": "Новое"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Новое"

    async def test_update_partial(self, async_client: AsyncClient) -> None:
        created = await async_client.post(
            "/api/menu/items",
            json={"title": "Тест", "url": "/test", "order": 5},
        )
        item_id = created.json()["id"]
        prev_data = created.json()

        resp = await async_client.put(
            f"/api/menu/items/{item_id}",
            json={"url": "/changed"},
        )
        data = resp.json()
        assert data["url"] == "/changed"
        assert data["title"] == prev_data["title"]
        assert data["order"] == prev_data["order"]

    async def test_update_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        resp = await async_client.put("/api/menu/items/9999", json={"title": "X"})
        assert resp.status_code == 404


class TestDelete:
    async def test_delete_existing(self, async_client: AsyncClient) -> None:
        created = await async_client.post(
            "/api/menu/items", json={"title": "Удалить"}
        )
        item_id = created.json()["id"]

        resp = await async_client.delete(f"/api/menu/items/{item_id}")
        assert resp.status_code == 204

        get_resp = await async_client.get(f"/api/menu/items/{item_id}")
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        resp = await async_client.delete("/api/menu/items/9999")
        assert resp.status_code == 404

    async def test_delete_cascade(self, async_client: AsyncClient) -> None:
        parent = await async_client.post(
            "/api/menu/items", json={"title": "P"}
        )
        parent_id = parent.json()["id"]
        await async_client.post(
            "/api/menu/items",
            json={"title": "C", "parent_id": parent_id},
        )

        # Delete parent
        await async_client.delete(f"/api/menu/items/{parent_id}")

        # Both should be gone
        list_resp = await async_client.get("/api/menu/items")
        assert len(list_resp.json()) == 0


class TestReorder:
    async def test_reorder_siblings(self, async_client: AsyncClient) -> None:
        a = (await async_client.post("/api/menu/items", json={"title": "A", "order": 0})).json()
        b = (await async_client.post("/api/menu/items", json={"title": "B", "order": 1})).json()

        resp = await async_client.put(
            "/api/menu/reorder",
            json=[
                {"id": a["id"], "order": 1, "parent_id": None},
                {"id": b["id"], "order": 0, "parent_id": None},
            ],
        )
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()]
        assert titles == ["B", "A"]

    async def test_reorder_nonexistent(self, async_client: AsyncClient) -> None:
        resp = await async_client.put(
            "/api/menu/reorder",
            json=[{"id": 9999, "order": 0, "parent_id": None}],
        )
        # Reorder with nonexistent IDs is accepted (no constraint violation expected)
        assert resp.status_code == 200


class TestTree:
    async def test_tree_structure(self, async_client: AsyncClient) -> None:
        parent = (
            await async_client.post("/api/menu/items", json={"title": "P"})
        ).json()
        child = (
            await async_client.post(
                "/api/menu/items",
                json={"title": "C", "parent_id": parent["id"]},
            )
        ).json()

        resp = await async_client.get("/api/menu/tree")
        assert resp.status_code == 200
        tree = resp.json()
        assert len(tree) == 1
        assert tree[0]["title"] == "P"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["title"] == "C"

    async def test_tree_active_only(self, async_client: AsyncClient) -> None:
        await async_client.post("/api/menu/items", json={"title": "Visible"})
        await async_client.post(
            "/api/menu/items", json={"title": "Hidden", "is_active": False}
        )

        resp = await async_client.get("/api/menu/tree", params={"active_only": True})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Visible"

        resp_all = await async_client.get("/api/menu/tree", params={"active_only": False})
        assert len(resp_all.json()) == 2


class TestDisplay:
    """'Site display' tests — the menu tree as rendered for the public site."""

    async def test_public_display_tree(self, async_client: AsyncClient) -> None:
        """The public site should get active items ordered correctly."""
        await async_client.post(
            "/api/menu/items",
            json={"title": "Главная", "url": "/", "order": 0},
        )
        school = (
            await async_client.post(
                "/api/menu/items",
                json={"title": "Школа", "url": "/school", "order": 1},
            )
        ).json()
        await async_client.post(
            "/api/menu/items",
            json={
                "title": "Новости школы",
                "url": "/school/news",
                "parent_id": school["id"],
                "order": 0,
            },
        )
        await async_client.post(
            "/api/menu/items",
            json={"title": "Контакты", "url": "/contacts", "order": 2, "is_active": False},
        )

        resp = await async_client.get("/api/menu/tree", params={"active_only": True})
        assert resp.status_code == 200
        tree = resp.json()

        assert len(tree) == 2
        assert tree[0]["title"] == "Главная"
        assert tree[1]["title"] == "Школа"
        assert len(tree[1]["children"]) == 1
        assert tree[1]["children"][0]["title"] == "Новости школы"

    async def test_empty_menu_display(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/api/menu/tree", params={"active_only": True})
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_multiple_children_ordered(self, async_client: AsyncClient) -> None:
        parent = (
            await async_client.post("/api/menu/items", json={"title": "Разделы"})
        ).json()
        await async_client.post(
            "/api/menu/items",
            json={"title": "C", "parent_id": parent["id"], "order": 2},
        )
        await async_client.post(
            "/api/menu/items",
            json={"title": "A", "parent_id": parent["id"], "order": 0},
        )
        await async_client.post(
            "/api/menu/items",
            json={"title": "B", "parent_id": parent["id"], "order": 1},
        )

        resp = await async_client.get("/api/menu/tree")
        children = resp.json()[0]["children"]
        assert [c["title"] for c in children] == ["A", "B", "C"]
