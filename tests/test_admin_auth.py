"""Tests for admin authentication — login, logout, and session protection."""

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.routers import auth
from app.services.auth import verify_credentials, is_authenticated

# ── Test helpers ────────────────────────────────────────────────────────────

_SESSION_SECRET = "test-secret-do-not-use-in-prod"
BASE_DIR = Path(__file__).resolve().parent.parent / "app"


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient with SessionMiddleware, auth router, and
    protected admin pages."""
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key=_SESSION_SECRET)
    app.include_router(auth.router)

    _templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

    @app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
    def _admin_index(request: Request):
        if not is_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin", status_code=302)
        return _templates.TemplateResponse(request=request, name="admin/menu.html")

    @app.get("/admin/menu", response_class=HTMLResponse, include_in_schema=False)
    def _admin_menu(request: Request):
        if not is_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/menu", status_code=302)
        return _templates.TemplateResponse(request=request, name="admin/menu.html")

    with TestClient(app) as c:
        yield c


# ── Service-level tests ─────────────────────────────────────────────────────


class TestVerifyCredentials:
    def test_correct_credentials(self) -> None:
        assert verify_credentials("admin", "admin123") is True

    def test_wrong_username(self) -> None:
        assert verify_credentials("hacker", "admin123") is False

    def test_wrong_password(self) -> None:
        assert verify_credentials("admin", "wrongpass") is False

    def test_both_wrong(self) -> None:
        assert verify_credentials("foo", "bar") is False

    def test_empty_username(self) -> None:
        assert verify_credentials("", "admin123") is False

    def test_empty_password(self) -> None:
        assert verify_credentials("admin", "") is False

    def test_empty_both(self) -> None:
        assert verify_credentials("", "") is False


# ── Login page rendering ────────────────────────────────────────────────────


class TestLoginPage:
    def test_login_page_renders(self, client: TestClient) -> None:
        resp = client.get("/admin/login")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Войдите в панель управления" in resp.text
        assert "password" in resp.text
        assert "username" in resp.text
        assert "csrf" not in resp.text.lower()  # no CSRF token

    def test_login_page_form_method(self, client: TestClient) -> None:
        resp = client.get("/admin/login")
        assert 'method="POST"' in resp.text
        assert '/admin/login' in resp.text

    def test_already_logged_in_redirects_to_admin(self, client: TestClient) -> None:
        """Already-authenticated users hitting /admin/login should bounce."""
        # Login first
        client.post("/admin/login", data={"username": "admin", "password": "admin123"})
        # Then try login page
        resp = client.get("/admin/login", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/menu"


# ── Login (POST) ────────────────────────────────────────────────────────────


class TestLoginPost:
    def test_successful_login_redirects(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/menu"

    def test_successful_login_sets_session_cookie(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )
        # Starlette's SessionMiddleware sets a signed cookie named "session"
        assert "session" in resp.cookies
        assert resp.cookies["session"] != ""

    def test_successful_login_allows_access_to_protected_page(
        self, client: TestClient
    ) -> None:
        """After login, a protected page should render instead of redirecting.
        TestClient automatically stores cookies between requests."""
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_wrong_password_returns_error(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert "Неверное имя пользователя или пароль" in resp.text

    def test_wrong_username_returns_error(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "hacker", "password": "admin123"},
        )
        assert resp.status_code == 401
        assert "Неверное имя пользователя или пароль" in resp.text

    def test_empty_credentials_returns_error(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "", "password": ""},
        )
        assert resp.status_code == 401
        assert "Неверное имя пользователя или пароль" in resp.text

    def test_missing_username_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"password": "admin123"},
        )
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login",
            data={"username": "admin"},
        )
        assert resp.status_code == 422

    def test_redirect_to_next_param(self, client: TestClient) -> None:
        """If ?next=/admin/menu is provided, redirect there after login."""
        resp = client.post(
            "/admin/login?next=/admin/menu",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/menu"

    def test_redirect_to_custom_next_param(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/login?next=/admin",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin"

    def test_remember_me_persistence(self, client: TestClient) -> None:
        """Session cookie should persist across requests (no logout)."""
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        # First request
        resp1 = client.get("/admin/menu", follow_redirects=False)
        assert resp1.status_code == 200

        # Second request — still authenticated
        resp2 = client.get("/admin/menu", follow_redirects=False)
        assert resp2.status_code == 200


# ── Logout ──────────────────────────────────────────────────────────────────


class TestLogout:
    def test_logout_redirects_to_login(self, client: TestClient) -> None:
        # Login first
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        resp = client.get("/admin/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/login"

    def test_logout_clears_session(self, client: TestClient) -> None:
        # Login (TestClient stores the cookie)
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        # Verify we can access protected page before logout
        before = client.get("/admin/menu", follow_redirects=False)
        assert before.status_code == 200

        # Logout
        client.get("/admin/logout")

        # After logout, access to protected page should redirect
        after = client.get("/admin/menu", follow_redirects=False)
        assert after.status_code == 302
        assert after.headers["location"] == "/admin/login?next=/admin/menu"

    def test_logout_without_session_still_works(self, client: TestClient) -> None:
        """Logging out without being logged in should not error."""
        resp = client.get("/admin/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/login"


# ── Protected routes ────────────────────────────────────────────────────────


class TestProtectedRoutes:
    def test_admin_menu_redirects_without_session(self, client: TestClient) -> None:
        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/login?next=/admin/menu"

    def test_admin_index_redirects_without_session(self, client: TestClient) -> None:
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["location"]

    def test_admin_slash_redirects_without_session(self, client: TestClient) -> None:
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["location"]

    def test_protected_page_with_valid_session(self, client: TestClient) -> None:
        """Login, then access protected page (cookies managed by TestClient)."""
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_protected_page_with_invalid_session_cookie(self, client: TestClient) -> None:
        """Tampered session cookie should be treated as no session.
        Set an invalid cookie on the client before making the request."""
        client.cookies.set("session", "tampered.invalid.cookie")
        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["location"]

    def test_full_login_flow(self, client: TestClient) -> None:
        """Complete flow: access protected → redirected → login → access
        → logout → blocked."""
        # Step 1: try protected page
        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["location"]

        # Step 2: login page renders
        resp = client.get("/admin/login")
        assert resp.status_code == 200

        # Step 3: submit login (TestClient stores the session cookie)
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
        )

        # Step 4: access protected page
        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 200

        # Step 5: logout
        client.get("/admin/logout")

        # Step 6: try protected page again
        resp = client.get("/admin/menu", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["location"]
