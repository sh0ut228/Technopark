from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from web.admin.router import router as admin_router
from bot.database import Database

app = FastAPI(
    title="MAX Bot Admin",
    description="Панель управления для бота в мессенджере MAX",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates = Jinja2Templates(directory=str(static_path))

app.include_router(admin_router, prefix="/api/admin")

db = Database()

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "MAX Bot Admin"}
    )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "MAX Bot Admin",
        "links_count": len(db.get_all_links()),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)