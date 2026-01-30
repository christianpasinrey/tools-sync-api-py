from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config.db import connect_db
from src.config.settings import settings
from src.middleware.error_handler import error_handler
from src.middleware.rate_limiter import limiter
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.routes.auth import router as auth_router
from src.routes.vault import router as vault_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown


app = FastAPI(
    title="Tools Sync API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# --- Middleware ---

# Security headers (like helmet)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global error handler
app.add_exception_handler(Exception, error_handler)

# --- Routes ---

app.include_router(auth_router)
app.include_router(vault_router)


@app.get("/")
async def root():
    return {"message": "Tools Sync API (Python)"}
