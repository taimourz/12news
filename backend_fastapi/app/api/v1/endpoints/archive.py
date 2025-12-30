from datetime import datetime, timedelta
from pathlib import Path
import json
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from app.services.scraper import ScraperService
from app.models.archive import DayArchive
from app.dependencies import get_scraper_service
from app.core.security import validate_api_key

router = APIRouter(prefix="/archive", tags=["archive"])

def load_fallback_data() -> DayArchive:
    fallback_path = Path("fallback_data/fallback.json")
    
    if not fallback_path.exists():
        raise HTTPException(
            status_code=503,
            detail="No data available and fallback file not found"
        )
    
    try:
        with open(fallback_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return DayArchive(**data)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to load fallback data: {str(e)}"
        )

@router.get("/today", response_model=DayArchive)
async def get_today(
    background_tasks: BackgroundTasks,
    scraper: ScraperService = Depends(get_scraper_service),
    _: None = Depends(validate_api_key)
):
    today = scraper.get_todays_date()
    
    deleted = await scraper.repository.delete_old_files(today)
    if deleted > 0:
        print(f"Deleted {deleted} old files")
    
    archive = await scraper.load_archive(today)
    
    if not archive:
        print(f"No data for today ({today}), loading fallback data")
        try:
            archive = load_fallback_data()
        except HTTPException:
            raise HTTPException(
                status_code=404, 
                detail=f"No data for today ({today}) and no fallback available"
            )
    
    background_tasks.add_task(scraper.ensure_tomorrow_exists)
    return archive

@router.get("/{date}", response_model=DayArchive)
async def get_date(
    date: str,
    background_tasks: BackgroundTasks,
    scraper: ScraperService = Depends(get_scraper_service),
    _: None = Depends(validate_api_key)
):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    archive = await scraper.load_archive(date)
    
    if not archive:
        print(f"Data not found for {date}, scraping...")
        try:
            archive = await scraper.scrape_day(date)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")
    
    async def precompute_next_day():
        try:
            next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            if not await scraper.repository.file_exists(next_day):
                await scraper.scrape_day(next_day)
        except Exception as e:
            print(f"Error precomputing: {e}")
    
    background_tasks.add_task(precompute_next_day)
    return archive