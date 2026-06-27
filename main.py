"""
FreeAPI Directory — Main Application
FastAPI server with Jinja2 templates, SQLite database, and Ollama AI Q&A.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, init_db
from models import Category, ApiEntry
from ollama_service import search_and_answer

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# ── App Lifecycle ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="FreeAPI Directory",
    description="A curated directory of free public APIs with AI-powered search.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Static & Templates ─────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_template(name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    """Render a Jinja2 template with context."""
    template = jinja_env.get_template(name)
    request = context.get("request")
    # Add 'url_for' for static files
    if request:
        context["url_for"] = app.url_path_for
    html = template.render(context)
    return HTMLResponse(content=html, status_code=status_code)

# ── Helpers ────────────────────────────────────────────────────────────────
async def get_all_categories(db: AsyncSession):
    """Return all categories ordered by sort_order, with apis eagerly loaded."""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.apis))
        .order_by(Category.sort_order)
    )
    return result.unique().scalars().all()


# ── Routes: Pages ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    """Homepage: category grid + featured APIs."""
    categories = await get_all_categories(db)

    # Fetch top 6 featured APIs across all categories
    featured_result = await db.execute(
        select(ApiEntry)
        .where(ApiEntry.status == "active")
        .options(selectinload(ApiEntry.category))
        .order_by(ApiEntry.updated_at.desc())
        .limit(6)
    )
    featured = featured_result.scalars().all()

    return render_template("index.html", {
        "request": request,
        "categories": categories,
        "featured": featured,
        "page_title": "FreeAPI Directory — 免费 API 资源导航",
    })


@app.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    """Category page: list all APIs under a category."""
    cat_result = await db.execute(
        select(Category).where(Category.slug == slug)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    apis_result = await db.execute(
        select(ApiEntry)
        .where(ApiEntry.category_id == category.id, ApiEntry.status == "active")
        .options(selectinload(ApiEntry.category))
        .order_by(ApiEntry.name)
    )
    apis = apis_result.scalars().all()

    all_categories = await get_all_categories(db)

    return render_template("category.html", {
        "request": request,
        "category": category,
        "apis": apis,
        "categories": all_categories,
        "page_title": f"{category.name} — FreeAPI Directory",
    })


@app.get("/api/categories")
async def api_categories(db: AsyncSession = Depends(get_db)):
    """Return all categories as JSON."""
    categories = await get_all_categories(db)
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "icon": c.icon,
            "description": c.description,
            "api_count": len(c.apis),
        }
        for c in categories
    ]


@app.get("/api/{api_id}", response_class=HTMLResponse)
async def api_detail(request: Request, api_id: int, db: AsyncSession = Depends(get_db)):
    """API detail page."""
    result = await db.execute(
        select(ApiEntry)
        .where(ApiEntry.id == api_id)
        .options(selectinload(ApiEntry.category))
    )
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(status_code=404, detail="API not found")

    all_categories = await get_all_categories(db)

    return render_template("detail.html", {
        "request": request,
        "api": api,
        "categories": all_categories,
        "page_title": f"{api.name} — FreeAPI Directory",
    })


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, db: AsyncSession = Depends(get_db)):
    """AI-powered search / Q&A page."""
    # Get a few random APIs across all categories as suggestions
    suggestions = await db.execute(
        select(ApiEntry)
        .where(ApiEntry.status == "active")
        .options(selectinload(ApiEntry.category))
        .order_by(func.random())
        .limit(8)
    )
    suggestion_list = suggestions.scalars().all()

    all_categories = await get_all_categories(db)

    return render_template("search.html", {
        "request": request,
        "categories": all_categories,
        "answer": None,
        "sources": None,
        "query": "",
        "suggestions": suggestion_list,
        "page_title": "AI 智能搜索 — FreeAPI Directory",
    })


# ── Routes: API Endpoints ──────────────────────────────────────────────────

@app.post("/api/ask")
async def api_ask(request: Request, db: AsyncSession = Depends(get_db)):
    """AI Q&A endpoint. Accepts JSON with 'query' field."""
    import json

    query = None

    # Read raw body first (only once), then try to parse
    raw = await request.body()

    # Try JSON with multiple encodings
    for enc in ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]:
        try:
            text = raw.decode(enc)
            data = json.loads(text)
            query = data.get("query", "").strip()
            if query:
                break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    # Last fallback: form data
    if not query:
        try:
            form_data = await request.form()
            query = form_data.get("query", "").strip()
        except Exception:
            pass

    if not query:
        return JSONResponse({"error": "Query cannot be empty"}, status_code=400)

    result = await search_and_answer(db, query)
    return JSONResponse(result)


# ── Error Handlers ─────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    all_categories = []
    try:
        async for db in get_db():
            all_categories = await get_all_categories(db)
            break
    except Exception:
        pass

    return render_template("404.html", {
        "request": request,
        "categories": all_categories,
        "page_title": "Page Not Found — FreeAPI Directory",
    }, status_code=404)


# ── Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
