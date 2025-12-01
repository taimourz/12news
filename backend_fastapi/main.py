import asyncio
import json
import pytz
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, TimeoutError as PlaywrightTimeoutError
import aiofiles

API_KEY = os.getenv("TAIMOUR_API_KEY")

def validate_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

PKT = pytz.timezone("Asia/Karachi")

class Article(BaseModel):
    title: str
    url: str
    summary: str
    section: str
    date: str
    imageUrl: Optional[str] = None

class DayArchive(BaseModel):
    date: str
    sections: Dict[str, List[Article]]
    cached_at: Optional[str] = None

class DawnScraper:
    def __init__(self):
        self.base_url = "https://www.dawn.com"
        self.data_dir = Path("./data")
        self.delay = 2
        self.cache: Dict[str, DayArchive] = {}
        self.max_retries = 2
        self.page_timeout = 45000

    async def fetch_page_with_browser(self, url: str) -> str:
        """Fetch a single page with its own isolated browser instance"""
        playwright = None
        browser = None
        page = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            print(f"  Fetching: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.page_timeout)
                await asyncio.sleep(3) 
            except PlaywrightTimeoutError:
                print(f"  Timeout on first attempt for {url}, retrying...")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.page_timeout)
                await asyncio.sleep(3)
            
            html = await page.content()
            return html
            
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except:
                    pass

    def resolve_image_url(self, article_soup) -> Optional[str]:
        """Extract image URL from article element"""
        picture = article_soup.find('picture')
        if picture:
            source = picture.find('source')
            if source:
                srcset = source.get('srcset')
                if srcset:
                    first_url = srcset.split(',')[0].strip().split(' ')[0]
                    if first_url and not first_url.startswith('data:'):
                        return first_url
        
        img = article_soup.find('img')
        if img:
            for attr in ['data-src', 'src', 'data-original']:
                url = img.get(attr)
                if url and not url.startswith('data:'):
                    return url
            
            srcset = img.get('srcset')
            if srcset:
                first_url = srcset.split(',')[0].strip().split(' ')[0]
                if first_url and not first_url.startswith('data:'):
                    return first_url
        
        return None

    def parse_section(self, html: str, section: str, date: str) -> List[Article]:
        """Parse articles from Dawn newspaper section"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        selectors = [
            'article.story',
            'article',
            '.story.block',
            'div.story',
            '.box.story',
        ]
        
        seen_titles = set()
        
        for selector in selectors:
            elements = soup.select(selector)
            
            if not elements:
                continue
            
            print(f"  Found {len(elements)} elements with selector: {selector}")
            
            for el in elements:
                title_el = el.select_one('h2 a, .story__link, h3 a, .story__title a, a.story__link')
                
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                url = title_el.get('href', '')
                
                if not title or not url:
                    continue
                
                if title in seen_titles:
                    continue
                
                seen_titles.add(title)
                
                summary_el = el.select_one('.story__excerpt, p, .story__text')
                summary = summary_el.get_text(strip=True) if summary_el else ''
                
                raw_image = self.resolve_image_url(el)
                image_url = None
                if raw_image:
                    if raw_image.startswith('//'):
                        image_url = f"https:{raw_image}"
                    elif raw_image.startswith('http'):
                        image_url = raw_image
                    elif raw_image.startswith('/'):
                        image_url = f"https://www.dawn.com{raw_image}"
                
                article_url = url
                if not url.startswith('http'):
                    if url.startswith('/'):
                        article_url = f"https://www.dawn.com{url}"
                    else:
                        article_url = f"https://www.dawn.com/{url}"
                
                article = Article(
                    title=title,
                    url=article_url,
                    summary=summary,
                    section=section,
                    date=date,
                    imageUrl=image_url
                )
                articles.append(article)
            
            if articles:
                break
        
        return articles

    async def scrape_section(self, section: str, date_string: str) -> tuple[List[Article], bool]:
        """Scrape a single section with retry logic. Returns (articles, success)"""
        url = f"{self.base_url}/newspaper/{section}/{date_string}"
        
        for attempt in range(self.max_retries):
            try:
                print(f"Scraping {section} for {date_string} (attempt {attempt + 1}/{self.max_retries})...")
                html = await self.fetch_page_with_browser(url)
                
                # Check if page exists (Dawn returns 200 even for missing dates)
                if "Page not found" in html or "404" in html or len(html) < 5000:
                    print(f"  Section {section} appears to be missing for this date")
                    return [], False
                
                articles = self.parse_section(html, section, date_string)
                print(f"  Found {len(articles)} articles")
                return articles, True
            except Exception as err:
                print(f"  Error on attempt {attempt + 1}: {err}")
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"  Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"  Failed to scrape {section} after {self.max_retries} attempts")
                    return [], False

    async def scrape_day(self, date_string: str) -> DayArchive:
        """Scrape all sections for a given day"""
        sections = [
            'front-page',
            'national',
            'business', 
            'international',
            'sport',
            'editorial',
            'back-page',
            'other-voices',
            'letters',
            'books-authors',
            'business-finance',
            'young-world',
            'sunday-magzine',
            'icon'
        ]
        
        day_archive = DayArchive(
            date=date_string,
            sections={},
            cached_at=datetime.now().isoformat()
        )
        
        # Scrape each section independently with delays between them
        for i, section in enumerate(sections):
            articles, success = await self.scrape_section(section, date_string)
            day_archive.sections[section] = articles
            
            if not success and len(articles) == 0:
                print(f"  Note: Section '{section}' may not exist for {date_string}")
            
            # Delay between sections
            if i < len(sections) - 1:
                await asyncio.sleep(self.delay)
        
        # Save to file
        await self.save_archive(day_archive)
        
        # Cache it
        self.cache[date_string] = day_archive
        
        return day_archive

    async def save_archive(self, day_archive: DayArchive):
        self.data_dir.mkdir(exist_ok=True)
        file_path = self.data_dir / f"{day_archive.date}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(day_archive.model_dump_json(indent=2))
        print(f"Archive saved to {file_path}")

    async def load_archive(self, date_string: str) -> Optional[DayArchive]:
        file_path = self.data_dir / f"{date_string}.json"
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            data = DayArchive.model_validate_json(content)
            self.cache[date_string] = data
            return data
        except Exception as e:
            print(f"Error loading archive for {date_string}: {e}")
            return None

    def get_todays_date(self) -> str:
        now = datetime.now(PKT)
        past = now.replace(year=now.year - 12)
        return past.strftime('%Y-%m-%d')

    def get_tomorrows_date(self) -> str:
        today_str = self.get_todays_date()
        today_dt = datetime.strptime(today_str, '%Y-%m-%d')
        tomorrow_dt = today_dt + timedelta(days=1)
        return tomorrow_dt.strftime('%Y-%m-%d')

    async def ensure_tomorrow_exists(self):
        """Scrape tomorrow's data if it doesn't exist"""
        tomorrow = self.get_tomorrows_date()
        file_path = self.data_dir / f"{tomorrow}.json"
        
        if file_path.exists():
            print(f"Tomorrow's data already exists: {tomorrow}")
            return
        
        print(f"Precomputing tomorrow's data: {tomorrow}")
        try:
            await self.scrape_day(tomorrow)
        except Exception as e:
            print(f"Error precomputing tomorrow: {e}")

scraper = DawnScraper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    yield

app = FastAPI(
    title="Dawn Archive API",
    description="API for scraping Dawn newspaper archives",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", dependencies=[Depends(validate_api_key)])
async def root():
    return {
        "message": "Dawn Archive API",
        "endpoints": {
            "/api/today": "Get today's articles (always cached)",
            "/api/date/{date}": "Get specific date (YYYY-MM-DD)",
            "/api/cache": "View cached dates",
            "/api/files": "View available data files",
            "/api/clear": "Delete all cached files"
        }
    }

@app.get("/api/today", dependencies=[Depends(validate_api_key)])
async def get_today(background_tasks: BackgroundTasks):
    """Get today's articles"""
    today = scraper.get_todays_date()
    
    data_dir = Path(scraper.data_dir)
    if data_dir.exists():
        for file in data_dir.glob("*.json"):
            try:
                file_date = file.stem
                if file_date < today:
                    file.unlink()
                    print(f"Deleted old file: {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
    
    archive = await scraper.load_archive(today)
    if not archive:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for today ({today}). Please ensure data files exist."
        )
    
    background_tasks.add_task(scraper.ensure_tomorrow_exists)
    
    return archive

@app.get("/api/date/{date}", dependencies=[Depends(validate_api_key)])
async def get_date(date: str, background_tasks: BackgroundTasks):
    """Get articles for a specific date"""
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Try loading from file first
    archive = await scraper.load_archive(date)
    if not archive:
        print(f"Data not found for {date}, scraping...")
        try:
            archive = await scraper.scrape_day(date)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping: {str(e)}")
    
    # Precompute next day in background
    async def precompute_next_day():
        try:
            requested_date = datetime.strptime(date, '%Y-%m-%d')
            next_day = (requested_date + timedelta(days=1)).strftime('%Y-%m-%d')
            file_path = scraper.data_dir / f"{next_day}.json"
            if not file_path.exists():
                print(f"Precomputing next day: {next_day}")
                await scraper.scrape_day(next_day)
        except Exception as e:
            print(f"Error precomputing next day: {e}")
    
    background_tasks.add_task(precompute_next_day)
    
    return archive

@app.get("/api/cache", dependencies=[Depends(validate_api_key)])
async def get_cache_info():
    """Get information about cached dates in memory"""
    return {
        "cached_dates": list(scraper.cache.keys()),
        "count": len(scraper.cache)
    }

@app.get("/api/files", dependencies=[Depends(validate_api_key)])
async def get_files_info():
    """Get information about available data files on disk"""
    data_dir = Path("./data")
    if not data_dir.exists():
        return {"files": [], "count": 0}
    
    files = sorted([f.stem for f in data_dir.glob("*.json")])
    return {
        "files": files,
        "count": len(files)
    }

@app.delete("/api/clear", dependencies=[Depends(validate_api_key)])
async def clear_all_files():
    """Delete all cached JSON files"""
    data_dir = Path("./data")
    if not data_dir.exists():
        return {"message": "Data directory does not exist, nothing to clear."}
    
    deleted_files = []
    errors = []
    
    for file in data_dir.glob("*.json"):
        try:
            file.unlink()
            deleted_files.append(file.name)
        except Exception as e:
            errors.append({"file": file.name, "error": str(e)})
    
    return {
        "message": "Cleared all cached files.",
        "deleted_files": deleted_files,
        "errors": errors
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)