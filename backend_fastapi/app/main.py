from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers
from app.dependencies import get_browser_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"API Key: {'SET' if settings.API_KEY else 'NOT SET'}")
    print(f"Proxy: {'ENABLED' if settings.PROXY_URL else 'DISABLED'}")
    print("=" * 50)
    yield
    print("\nShutting down, closing browser...")
    browser = await get_browser_manager()
    await browser.close()
    print("Browser closed successfully")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for scraping Dawn newspaper archives",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
register_exception_handlers(app)

@app.get("/")
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} v{settings.VERSION}",
        "docs": "/docs",
        "endpoints": {
            "today": f"{settings.API_V1_PREFIX}/archive/today",
            "date": f"{settings.API_V1_PREFIX}/archive/{{date}}",
            "cache": f"{settings.API_V1_PREFIX}/cache",
            "files": f"{settings.API_V1_PREFIX}/cache/files",
            "clear": f"{settings.API_V1_PREFIX}/cache/clear"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7860,
        reload=True
    )