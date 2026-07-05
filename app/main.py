from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import menu

app = FastAPI(title="Золотаревка-сайт", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent

# ── Static files ─────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Jinja2 templates ─────────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ── Admin routes ─────────────────────────────────────────────────────────
@app.get("/admin/menu", response_class=HTMLResponse, include_in_schema=False)
def admin_menu_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="admin/menu.html"
    )


app.include_router(menu.router)
