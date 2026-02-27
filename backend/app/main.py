"""VIGILANT - FastAPI Application Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.api.dashboard import dashboard_router
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

from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import traceback
    print("====== FASTAPI VALIDATION ERROR ======")
    print(exc.errors())
    return JSONResponse(
        status_code=400,
        content={"detail": "FastAPI Validation Error", "body": exc.body, "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print("====== GLOBAL EXCEPTION CAUGHT ======")
    traceback.print_exc()
    return JSONResponse(status_code=400, content={"detail": f"Global intercept: {str(exc)}"})

# Register routes
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=f"{settings.API_PREFIX}/dashboard", tags=["dashboard"])


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
