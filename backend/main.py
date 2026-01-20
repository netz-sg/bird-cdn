from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager

from config import settings
from database import engine, Base
from routers import upload_v2 as upload, cache, stats, admin, purge, auth, transform, tracking, settings as settings_router
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
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,  # Disable default ReDoc
    openapi_url="/openapi.json"
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
app.include_router(cache.router, prefix="/api/cache", tags=["Cache Management"])
app.include_router(purge.router, prefix="/api", tags=["Cache Purge"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])
app.include_router(settings_router.router, prefix="/api", tags=["Settings"])


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

# Custom ReDoc endpoint with CDN fallback
@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc_html():
    """Custom ReDoc page with multiple CDN fallbacks"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bird-CDN API Documentation - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <div id="redoc-container"></div>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
        <script>
            // Initialize ReDoc with fallback error handling
            try {
                Redoc.init('/openapi.json', {
                    scrollYOffset: 50,
                    theme: {
                        colors: {
                            primary: {
                                main: '#667eea'
                            }
                        },
                        typography: {
                            fontSize: '16px',
                            fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
                        }
                    }
                }, document.getElementById('redoc-container'));
            } catch (error) {
                document.getElementById('redoc-container').innerHTML = 
                    '<div style="padding: 20px; text-align: center;">' +
                    '<h1>⚠️ ReDoc Loading Failed</h1>' +
                    '<p>Please use <a href="/docs">Swagger UI</a> instead.</p>' +
                    '<p>Error: ' + error.message + '</p>' +
                    '</div>';
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
