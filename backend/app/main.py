"""SENTINEL - FastAPI Application Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.api.dashboard import dashboard_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("=" * 60)
    print(f"  🛡️  SENTINEL v{settings.APP_VERSION}")
    print(f"  {settings.APP_DESCRIPTION}")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    print("[✓] Database initialized")
    
    # Load ML models
    try:
        from app.engine.detector import fraud_engine
        fraud_engine.load_models()
        print(f"[✓] Fraud model: {fraud_engine.fraud_model_version}")
        print(f"[✓] Chargeback model: {fraud_engine.chargeback_model_version}")
    except Exception as e:
        print(f"[!] Model loading deferred: {e}")

    print("=" * 60)
    print("[✓] SENTINEL is ready for fraud detection")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("[✓] SENTINEL shutting down")


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
        "service": "SENTINEL",
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": f"{settings.API_PREFIX}/assess",
    }
