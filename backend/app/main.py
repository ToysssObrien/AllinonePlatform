from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db, list_accounts, seed_demo_data
from .telegram_gateway import TelegramGateway
from .facebook_gateway import FacebookGateway
from .realtime import hub, router as ws_router
from .attachment import set_media_dir
from .routes.auth import is_authenticated, router as auth_router, SESSION_COOKIE_NAME
from .routes.accounts import configure as configure_accounts
from .routes.accounts import router as accounts_router
from .routes.chats import configure as configure_chats
from .routes.chats import router as chats_router
from .routes.messages import configure as configure_messages
from .routes.messages import router as messages_router
from .routes.webhook import configure as configure_webhook
from .routes.webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("omnidesk")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PROJECT_DIR = BASE_DIR.parents[1]
MEDIA_DIR = PROJECT_DIR / "data" / "media"
ENV_FILE = PROJECT_DIR / ".env"


def load_environment_file(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE pairs from a local .env file if present."""
    if not path.exists():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception as error:
        logger.warning("Failed to load .env file at %s: %s", path, error)


load_environment_file()

gateway = TelegramGateway()
gateway.set_event_sink(hub.broadcast)

fb_gateway = FacebookGateway()
fb_gateway.set_event_sink(hub.broadcast)

# Paths that do NOT require authentication
PUBLIC_PATHS = {
    "/login",
    "/api/auth/login",
    "/api/health",
}
PUBLIC_PREFIXES = (
    "/static/",
    "/api/webhook/",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    set_media_dir(MEDIA_DIR)
    configure_accounts(gateway=gateway, fb_gateway=fb_gateway, media_dir=str(MEDIA_DIR), broadcast=hub.broadcast)
    configure_chats(gateway=gateway, broadcast=hub.broadcast)
    configure_messages(gateway=gateway, fb_gateway=fb_gateway, broadcast=hub.broadcast)
    configure_webhook(fb_gateway=fb_gateway, media_dir=str(MEDIA_DIR))
    init_db()
    seed_demo_data()
    await gateway.prime_live_clients(list_accounts())
    logger.info("OmniDesk started")
    yield
    await gateway.close_all_clients()
    await fb_gateway.close()
    logger.info("OmniDesk stopped")


app = FastAPI(title="OmniDesk", lifespan=lifespan)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Redirect unauthenticated users to /login for page requests,
    or return 401 for API requests."""
    path = request.url.path

    # Allow public paths through
    if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return await call_next(request)

    # Check authentication
    if not is_authenticated(request):
        # API requests get a 401 JSON response
        if path.startswith("/api/") or path.startswith("/ws/"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        # Page requests get redirected to login
        return RedirectResponse(url="/login", status_code=302)

    return await call_next(request)


app.include_router(auth_router)
app.include_router(ws_router)
app.include_router(accounts_router)
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(webhook_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
