import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select

from app.database import Base, engine
from app.models import MenuItem, Page, MediaItem, Setting, Suggestion  # noqa: F401 — register models with Base
from app.routers import auth, menu, page, public, admin_tools
from app.services.auth import is_authenticated

app = FastAPI(title="Золотаревка-сайт", version="0.1.0")

# ── Session middleware (for admin auth) ──────────────────────────────────
_SESSION_SECRET = os.environ.get(
    "SESSION_SECRET",
    "change-me-in-production-use-a-long-random-string",
)
app.add_middleware(SessionMiddleware, secret_key=_SESSION_SECRET)

BASE_DIR = Path(__file__).resolve().parent

# ── Static files ─────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Jinja2 templates ─────────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Register a template global so all templates can access the menu without
# each route handler having to pass it manually.
def _inject_menu() -> list[dict]:
    """Template-callable: returns the active menu tree as nested dicts."""
    return _load_menu_dicts()

templates.env.globals["get_menu"] = _inject_menu


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ── Template context helpers ─────────────────────────────────────────────
def _load_menu_dicts() -> list[dict]:
    """Load the active menu tree as a list of nested dicts for Jinja2."""
    from app.database import SessionLocal
    from app.services.menu import get_active_menu_tree

    db = SessionLocal()
    try:
        tree = get_active_menu_tree(db)
        return _tree_to_dicts(tree)
    finally:
        db.close()


def _tree_to_dicts(nodes) -> list[dict]:
    """Convert MenuItemTreeNode Pydantic objects to plain dicts."""
    result = []
    for node in nodes:
        result.append({
            "id": node.id,
            "title": node.title,
            "url": node.url,
            "type": node.type,
            "children": _tree_to_dicts(node.children),
        })
    return result


# ── Admin routes ─────────────────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
def admin_index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/admin", status_code=302)
    return templates.TemplateResponse(
        request=request, name="admin/menu.html"
    )


@app.get("/admin/menu", response_class=HTMLResponse, include_in_schema=False)
def admin_menu_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/admin/menu", status_code=302)
    return templates.TemplateResponse(
        request=request, name="admin/menu.html"
    )


app.include_router(auth.router)
app.include_router(menu.router, prefix="/api")
app.include_router(page.router, prefix="/api")
app.include_router(public.router)
app.include_router(admin_tools.router)


# ── Admin pages (sidebar targets) ─────────────────────────────────────────
# Simple placeholder pages for admin sections that don't have full UIs yet.


@app.get("/admin/media", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/content", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/settings-page", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/roles-page", response_class=HTMLResponse, include_in_schema=False)
def admin_placeholder(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url=f"/admin/login?next={request.url.path}", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="admin/menu.html",
        context={"page_title": "Админ-панель"},
    )


# ── Public page routes (Jinja2) ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def web_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"page_title": "Главная"},
    )


@app.get("/{slug:path}", response_class=HTMLResponse, include_in_schema=False)
def web_page(slug: str, request: Request):
    # Skip internal paths
    if slug.startswith("api/") or slug.startswith("static") or slug in ("admin/",):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Not found"}, status_code=404)

    slug = slug.rstrip("/").split("/")[-1]

    # Try to load page content from database
    from app.database import SessionLocal
    from app.models import Page as PageModel

    db = SessionLocal()
    try:
        page = db.query(PageModel).filter(PageModel.slug == slug, PageModel.is_published == True).first()
    finally:
        db.close()

    if page:
        return templates.TemplateResponse(
            request=request,
            name="page.html",
            context={
                "page_title": page.title,
                "slug": slug,
                "page_content": page.content,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={
            "page_title": slug.capitalize(),
            "slug": slug,
            "page_content": "",
        },
    )


# ── Catch-all for non-GET methods on unknown paths ───────────────────────
# Without this, POST/PUT/DELETE to e.g. /login returns 405 (from the
# catch-all GET route matching the path pattern). We want 404 instead.
from fastapi.responses import JSONResponse as _JsonResponse


@app.api_route("/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
def method_not_allowed_fallback(path: str, request: Request):
    return _JsonResponse({"error": "Not found"}, status_code=404)
