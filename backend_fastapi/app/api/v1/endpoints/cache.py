from fastapi import APIRouter, Depends
from app.dependencies import get_scraper_service
from app.services.scraper import ScraperService
from app.core.security import validate_api_key

router = APIRouter(prefix="/cache", tags=["cache"])

@router.get("/")
async def get_cache_info(
    scraper: ScraperService = Depends(get_scraper_service),
    _: None = Depends(validate_api_key)
):
    return {
        "cached_dates": list(scraper.cache.keys()),
        "count": len(scraper.cache)
    }

@router.get("/files")
async def get_files_info(
    scraper: ScraperService = Depends(get_scraper_service),
    _: None = Depends(validate_api_key)
):
    dates = await scraper.repository.list_all_dates()
    return {"files": dates, "count": len(dates)}

@router.delete("/clear")
async def clear_all_files(
    scraper: ScraperService = Depends(get_scraper_service),
    _: None = Depends(validate_api_key)
):
    deleted_count, errors = await scraper.repository.delete_all_files()
    return {
        "deleted_count": deleted_count,
        "errors": errors
    }