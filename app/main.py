from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.database import Base, engine
from app.models import MenuItem
from app.routers import menu, public

app = FastAPI(title="Золотаревка-сайт", version="0.1.0")

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
@app.get("/admin/menu", response_class=HTMLResponse, include_in_schema=False)
def admin_menu_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="admin/menu.html"
    )


app.include_router(menu.router, prefix="/api")
app.include_router(public.router)


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
    if slug.startswith("api/") or slug.startswith("admin") or slug.startswith("static"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Not found"}, status_code=404)

    slug = slug.rstrip("/").split("/")[-1]
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={
            "page_title": slug.capitalize(),
            "slug": slug,
        },
    )
