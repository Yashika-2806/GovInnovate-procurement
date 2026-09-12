import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router as api_router
from src.config.settings import get_settings
from src.repositories.database import init_db
from src.services.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
# Windows consoles/pipes often default to cp1252; verified opportunity titles contain
# real Unicode (e.g. U+2011 non-breaking hyphen). Make log output degrade gracefully
# instead of crashing the server with UnicodeEncodeError.
for _h in logging.getLogger().handlers:
    _stream = getattr(_h, "stream", None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(errors="backslashreplace")
        except (ValueError, OSError):
            pass
logger = logging.getLogger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Starting background scheduler...")
    start_scheduler()
    logger.info(f"Verified Problem & Challenge Discovery Agent running on {settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
    logger.info("Shutting down background scheduler...")
    shutdown_scheduler()


app = FastAPI(
    title="Verified Problem & Challenge Discovery Agent",
    description="LangGraph-powered agent discovering, verifying, extracting, explaining, and monitoring genuine publicly published solution-seeking opportunities. Part of Team ALPHA's SIH multi-agent platform (SIH26136).",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend / downstream multi-agent access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "database_fallback_sqlite": settings.USE_SQLITE_FALLBACK
    }


# Serve the minimal read-only demo UI (registered LAST so /health and /api/* win).
# html=True makes "/" resolve to frontend/index.html.
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
else:
    logger.warning("Frontend directory not found at %s; UI will not be served.", _frontend_dir)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=True)
