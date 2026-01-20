from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from database import engine, Base
from routers import upload_v2 as upload, cache, stats, admin, purge, auth, watermark, transform, tracking
from metrics import PrometheusMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting CDN Backend API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    yield
    
    # Shutdown
    print("👋 Shutting down CDN Backend API...")


app = FastAPI(
    title="Bird-CDN Management API",
    description="Backend API für Bird-CDN - Upload, Cache Management & Analytics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Production: spezifische Domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics Middleware
app.add_middleware(PrometheusMiddleware)


# Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "path": request.url.path
        }
    )


# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(transform.router, prefix="/api", tags=["Image Transform"])
app.include_router(watermark.router, prefix="/api/watermark", tags=["Watermark"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache Management"])
app.include_router(purge.router, prefix="/api", tags=["Cache Purge"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])


# Health Check
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint für Container-Monitoring"""
    return {
        "status": "healthy",
        "service": "cdn-backend-api",
        "version": "1.0.0"
    }


# Metrics Endpoint für Prometheus
@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


# Root Endpoint
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "� Bird-CDN Management API",
        "docs": "/docs",
        "health": "/api/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
