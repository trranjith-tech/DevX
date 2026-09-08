import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import register_exception_handlers
from app.routers import ai, auth, interactions, metrics, replay, screenshots, session

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger("devx")

app = FastAPI(
    title="DevX Backend API",
    description="AI-powered mobile developer testing platform backend (in-memory prototype, no database)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(session.router)
app.include_router(metrics.router)
app.include_router(interactions.router)
app.include_router(screenshots.router)
app.include_router(ai.router)
app.include_router(replay.router)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("%s starting up (in-memory store, no external database)", settings.app_name)


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"success": True, "message": f"{settings.app_name} is running"}


@app.get("/health/db", tags=["Health"])
def health_db() -> dict:
    # No real database in this prototype — the in-memory store is always "up"
    # for as long as the process is running.
    return {"success": True, "message": "In-memory store is available (no external database configured)"}
