"""Integration tests for the page FastAPI endpoints via TestClient."""
# mypy: disable-error-code="arg-type"


# ── Helpers ────────────────────────────────────────────────────────────────

_SAMPLE_PAGE = {
    "title": "О школе",
    "slug": "o-shkole",
    "content": "<p>Наша школа основана в 1985 году.</p>",
    "is_published": True,
    "order": 0,
}

_SAMPLE_PAGE_2 = {
    "title": "Контакты",
    "slug": "kontakty",
    "content": "<p>Свяжитесь с нами.</p>",
    "is_published": True,
    "order": 1,
}


def _create_page(client, **overrides):
    """Helper: POST a page and return the response."""
    data = {**_SAMPLE_PAGE, **overrides}
    return client.post("/api/pages", json=data)


# ═══════════════════════════════════════════════════════════════════════════
# TestCreate
# ═══════════════════════════════════════════════════════════════════════════


class TestCreate:
    def test_create_page(self, page_client) -> None:
        resp = _create_page(page_client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "О школе"
        assert data["slug"] == "o-shkole"
        assert data["content"] == "<p>Наша школа основана в 1985 году.</p>"
        assert data["is_published"] is True
        assert data["order"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_page_without_content(self, page_client) -> None:
        resp = _create_page(page_client, content="")
        assert resp.status_code == 201
        assert resp.json()["content"] == ""

    def test_create_unpublished(self, page_client) -> None:
        resp = _create_page(page_client, is_published=False)
        assert resp.status_code == 201
        assert resp.json()["is_published"] is False

    def test_create_invalid_empty_title(self, page_client) -> None:
        resp = page_client.post("/api/pages", json={"title": "", "slug": "empty"})
        assert resp.status_code == 422

    def test_create_invalid_empty_slug(self, page_client) -> None:
        resp = page_client.post("/api/pages", json={"title": "Test", "slug": ""})
        assert resp.status_code == 422

    def test_create_duplicate_slug(self, page_client) -> None:
        _create_page(page_client)
        resp = _create_page(page_client)
        assert resp.status_code == 409


# ═══════════════════════════════════════════════════════════════════════════
# TestRead
# ═══════════════════════════════════════════════════════════════════════════


class TestRead:
    def test_get_page_by_id(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.get(f"/api/pages/{page_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "О школе"

    def test_get_nonexistent_returns_404(self, page_client) -> None:
        resp = page_client.get("/api/pages/9999")
        assert resp.status_code == 404

    def test_list_pages(self, page_client) -> None:
        _create_page(page_client)
        _create_page(page_client, **_SAMPLE_PAGE_2)

        resp = page_client.get("/api/pages")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_empty(self, page_client) -> None:
        resp = page_client.get("/api/pages")
        assert resp.status_code == 200
        assert resp.json() == []


# ═══════════════════════════════════════════════════════════════════════════
# TestUpdate
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdate:
    def test_update_title(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"title": "О школе (обновлено)"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "О школе (обновлено)"

    def test_update_content(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"content": "<p>Новое содержание</p>"}
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "<p>Новое содержание</p>"

    def test_update_slug(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"slug": "o-shkole-obnovleno"}
        )
        assert resp.status_code == 200
        assert resp.json()["slug"] == "o-shkole-obnovleno"

    def test_update_partial_keeps_other_fields(self, page_client) -> None:
        created = _create_page(
            page_client,
            content="<p>Original</p>",
            order=5,
        )
        page_id = created.json()["id"]

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"title": "Новое название"}
        )
        data = resp.json()
        assert data["title"] == "Новое название"
        assert data["content"] == "<p>Original</p>"
        assert data["order"] == 5
        assert data["slug"] == "o-shkole"

    def test_update_toggle_publish(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"is_published": False}
        )
        assert resp.status_code == 200
        assert resp.json()["is_published"] is False

        resp = page_client.put(
            f"/api/pages/{page_id}", json={"is_published": True}
        )
        assert resp.status_code == 200
        assert resp.json()["is_published"] is True

    def test_update_nonexistent_returns_404(self, page_client) -> None:
        resp = page_client.put(
            "/api/pages/9999", json={"title": "X"}
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# TestDelete
# ═══════════════════════════════════════════════════════════════════════════


class TestDelete:
    def test_delete_existing(self, page_client) -> None:
        created = _create_page(page_client)
        page_id = created.json()["id"]

        resp = page_client.delete(f"/api/pages/{page_id}")
        assert resp.status_code == 204

        get_resp = page_client.get(f"/api/pages/{page_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, page_client) -> None:
        resp = page_client.delete("/api/pages/9999")
        assert resp.status_code == 404

    def test_delete_then_list(self, page_client) -> None:
        p1 = _create_page(page_client).json()
        _create_page(page_client, **_SAMPLE_PAGE_2)

        page_client.delete(f"/api/pages/{p1['id']}")

        list_resp = page_client.get("/api/pages")
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["title"] == "Контакты"


# ═══════════════════════════════════════════════════════════════════════════
# TestReorder
# ═══════════════════════════════════════════════════════════════════════════


class TestReorder:
    def test_reorder(self, page_client) -> None:
        p1 = _create_page(page_client, order=0).json()
        p2 = _create_page(page_client, slug="kontakty", title="Контакты",
                          content="<p>Свяжитесь с нами.</p>", order=1).json()

        resp = page_client.post(
            "/api/pages/reorder",
            json=[
                {"id": p1["id"], "order": 1},
                {"id": p2["id"], "order": 0},
            ],
        )
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()]
        assert titles == ["Контакты", "О школе"]

    def test_reorder_nonexistent(self, page_client) -> None:
        resp = page_client.post(
            "/api/pages/reorder",
            json=[{"id": 9999, "order": 0}],
        )
        assert resp.status_code == 200

    def test_reorder_empty_list(self, page_client) -> None:
        resp = page_client.post("/api/pages/reorder", json=[])
        assert resp.status_code == 200
        assert resp.json() == []
