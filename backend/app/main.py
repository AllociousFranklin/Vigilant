"""VIGILANT - FastAPI Application Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.db.database import init_db
from app.engine.detector import detection_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("=" * 60)
    print(f"  🛡️  VIGILANT v{settings.APP_VERSION}")
    print(f"  {settings.APP_DESCRIPTION}")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    print("[✓] Database initialized")
    
    # Load ML models
    detection_engine.load_models()
    print(f"[✓] URL model: {detection_engine.url_model_version}")
    print(f"[✓] NLP model: {detection_engine.nlp_model_version}")
    print("=" * 60)
    print("[✓] VIGILANT is ready for threat detection")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("[✓] VIGILANT shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "VIGILANT",
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": f"{settings.API_PREFIX}/scan",
    }
