import asyncio
import json
import pytz
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext
import aiofiles
import re

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

class FingerprintGenerator:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
    ]
    
    @staticmethod
    def get_random_fingerprint():
        return {
            "user_agent": random.choice(FingerprintGenerator.USER_AGENTS),
            "viewport": random.choice(FingerprintGenerator.SCREEN_RESOLUTIONS),
            "screen": random.choice(FingerprintGenerator.SCREEN_RESOLUTIONS),
        }

class DawnScraper:
    def __init__(self):
        self.base_url = "https://www.dawn.com/newspaper"
        self.data_dir = Path("./data")
        self.delay = 3
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.cache: Dict[str, DayArchive] = {}
        self.proxy_url = os.getenv("PROXY_URL")

    async def init_browser(self):
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--start-maximized',
                ]
            )
        return self.browser

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def create_stealth_context(self) -> BrowserContext:
        browser = await self.init_browser()
        fingerprint = FingerprintGenerator.get_random_fingerprint()
        
        proxy_config = None
        if self.proxy_url:
            proxy_str = self.proxy_url

            m = re.match(r"http://([^:]+):([^@]+)@(.+)", proxy_str)
            if not m:
                raise ValueError(f"Invalid PROXY_URL format: {proxy_str}")

            username, password, server = m.groups()
            proxy_config = {
                "server": f"http://{server}",
                "username": username,
                "password": password
            }
        
        context = await browser.new_context(
            viewport=fingerprint["viewport"],
            screen=fingerprint["screen"],
            user_agent=fingerprint["user_agent"],
            locale="en-US",
            timezone_id="Asia/Karachi",
            proxy=proxy_config,
            permissions=["geolocation"],
            geolocation={"latitude": 33.6844, "longitude": 73.0479},  # Rawalpindi coords
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Cache-Control": "max-age=0",
                "DNT": "1"
            }
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            delete navigator.__proto__.webdriver;
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format',
                        length: 1
                    },
                    {
                        name: 'Chrome PDF Viewer',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: '',
                        length: 1
                    },
                    {
                        name: 'Native Client',
                        filename: 'internal-nacl-plugin',
                        description: '',
                        length: 2
                    }
                ],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const dataURL = originalToDataURL.apply(this, arguments);
                // Add subtle noise to prevent canvas fingerprinting
                return dataURL;
            };
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0
                })
            });
            
            delete window.playwright;
            delete window._playwright;
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 100,
                    downlink: 10,
                    saveData: false
                })
            });
            
            const originalDebug = console.debug;
            console.debug = function() {
                if (arguments[0] && arguments[0].includes('Playwright')) {
                    return;
                }
                return originalDebug.apply(console, arguments);
            };
        """)
        
        return context

    def resolve_image_url(self, article_soup) -> Optional[str]:
        img = article_soup.find('img')
        picture = article_soup.find('picture')

        if img:
            for attr in ['data-src', 'data-original', 'data-lazy-src']:
                url = img.get(attr)
                if url and not url.startswith('data:image'):
                    return url

            srcset = img.get('srcset')
            if srcset:
                first = srcset.split(',')[0].strip().split(' ')[0]
                if not first.startswith('data:image'):
                    return first

        if picture:
            source = picture.find('source')
            if source:
                srcset = source.get('srcset')
                if srcset:
                    first = srcset.split(',')[0].strip().split(' ')[0]
                    return first

        if img:
            url = img.get('src')
            if url and not url.startswith('data:image'):
                return url

        return None

    async def fetch_page(self, url: str, retry_count: int = 0) -> str:
        max_retries = 2
        
        context = await self.create_stealth_context()
        page = await context.new_page()

        print(f"  Fetching: {url} (attempt {retry_count + 1}/{max_retries + 1})")
        
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            response = await page.goto(
                url, 
                wait_until="domcontentloaded",
                timeout=90000
            )
            
            status = response.status if response else "No response"
            print(f"  Response status: {status}")
            
            if response and response.status == 403:
                print(f"  Got 403, retrying with fresh context...")
                await page.close()
                await context.close()
                
                if retry_count < max_retries:
                    await asyncio.sleep(random.uniform(3, 5))
                    return await self.fetch_page(url, retry_count + 1)
                else:
                    raise Exception(f"Failed after {max_retries + 1} attempts: 403 Forbidden")
            
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            try:
                await page.wait_for_selector(
                    'article, .story, .box, [class*="story"]',
                    timeout=10000
                )
                print(f"Content loaded successfully")
            except Exception as wait_err:
                print(f"Timeout waiting for content: {wait_err}")
            
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;

                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            
            await asyncio.sleep(random.uniform(1, 2))
            html = await page.content()
            
            if len(html) < 5000:
                print(f"WARNING: Suspiciously short HTML!")
                debug_path = self.data_dir / f"debug_blocked_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                self.data_dir.mkdir(exist_ok=True)
                async with aiofiles.open(debug_path, 'w', encoding='utf-8') as f:
                    await f.write(html)
                print(f"  Saved to: {debug_path}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            await page.close()
            await context.close()
            
            if retry_count < max_retries:
                await asyncio.sleep(random.uniform(3, 5))
                return await self.fetch_page(url, retry_count + 1)
            raise
        
        await page.close()
        await context.close()
        return html

    def parse_section(self, html: str, section: str, date: str) -> List[Article]:
        soup = BeautifulSoup(html, 'html.parser')
        articles = []

        selectors = [
            'article.story',
            'article[class*="story"]',
            '.story.box',
            '.story',
            'article',
            '.box.story',
            '.story-list article',
            'div[class*="story"]',
            '.article-box',
            '[data-story-id]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            
            if not elements:
                continue

            for el in elements:
                title_el = el.select_one(
                    'h2 a, .story__title a, h3 a, .story__link, '
                    'a.story__link, [class*="title"] a, h2, h3'
                )
                
                summary_el = el.select_one(
                    '.story__excerpt, .story__text, .excerpt, '
                    '[class*="excerpt"], p, .description'
                )

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get('href') if title_el.name == 'a' else None
                
                if not url:
                    link = el.find('a')
                    url = link.get('href') if link else None
                
                summary = summary_el.get_text(strip=True) if summary_el else ''

                if not title or not url:
                    continue

                if any(a.title == title for a in articles):
                    continue

                raw_image = self.resolve_image_url(el)
                image_url = None
                if raw_image:
                    if raw_image.startswith('//'):
                        image_url = f"https:{raw_image}"
                    elif raw_image.startswith('http'):
                        image_url = raw_image
                    else:
                        image_url = f"https://www.dawn.com{raw_image}"
                article_url = url if url.startswith('http') else f"https://www.dawn.com{url}"
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

    async def scrape_day(self, date_string: str) -> DayArchive:
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

        await self.init_browser()

        for section in sections:
            print(f"Scraping {section} for {date_string}...")
            try:
                url = f"{self.base_url}/{section}/{date_string}"
                html = await self.fetch_page(url)
                articles = self.parse_section(html, section, date_string)

                day_archive.sections[section] = articles
                print(f"  ✓ Found {len(articles)} articles in {section}")

                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as err:
                print(f"✗ Failed to scrape {section}: {err}")
                day_archive.sections[section] = []

        await self.close_browser()
        await self.save_archive(day_archive)
        self.cache[date_string] = day_archive

        return day_archive

    async def save_archive(self, day_archive: DayArchive):
        self.data_dir.mkdir(exist_ok=True)
        file_path = self.data_dir / f"{day_archive.date}.json"

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(day_archive.model_dump_json(indent=2))

        print(f"Archive saved to {file_path}")

    async def load_archive(self, date_string: str) -> Optional[DayArchive]:
        file_path = self.data_dir / f"{date_string}.json"
        if not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
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
    print("=" * 50)
    print(f"Dawn Scraper")
    print(f"Startup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if scraper.proxy_url:
        print(f"Proxy: ENABLED")
    else:
        print(f"Proxy: DISABLED (set PROXY_URL env var to enable)")
    print("=" * 50)
    yield
    print("Shutting down, closing browser...")
    await scraper.close_browser()

app = FastAPI(
    title="Dawn Archive API",
    description="API for scraping Dawn newspaper",
    version="3.0.0",
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
        "message": "Dawn Archive API v3.0 - Advanced Anti-Detection Edition",
        "features": [
            "Advanced fingerprint spoofing",
            "WebGL & Canvas randomization", 
            "Navigator property masking",
            "Human-like behavior simulation",
            "Optional proxy support",
            "Auto-retry on 403"
        ],
        "endpoints": {
            "/api/today": "Get today's articles",
            "/api/date/{date}": "Get specific date (YYYY-MM-DD)",
            "/api/cache": "View cached dates",
            "/api/files": "View available files",
            "/api/clear": "Delete all cached files"
        }
    }

@app.get("/api/today", dependencies=[Depends(validate_api_key)])
async def get_today(background_tasks: BackgroundTasks):
    today = scraper.get_todays_date()
    
    data_dir = Path(scraper.data_dir)
    if data_dir.exists():
        for file in data_dir.glob("*.json"):
            try:
                if file.stem < today:
                    file.unlink()
            except Exception as e:
                print(f"Error deleting {file}: {e}")
    
    archive = await scraper.load_archive(today)
    if not archive:
        raise HTTPException(
            status_code=404, 
            detail=f"No data for today ({today})"
        )
    
    background_tasks.add_task(scraper.ensure_tomorrow_exists)
    return archive

@app.get("/api/date/{date}", dependencies=[Depends(validate_api_key)])
async def get_date(date: str, background_tasks: BackgroundTasks):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    archive = await scraper.load_archive(date)
    if not archive:
        print(f"Data not found for {date}, scraping...")
        try:
            archive = await scraper.scrape_day(date)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    async def precompute_next_day():
        try:
            next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            if not (scraper.data_dir / f"{next_day}.json").exists():
                await scraper.scrape_day(next_day)
        except Exception as e:
            print(f"Error precomputing: {e}")
    
    background_tasks.add_task(precompute_next_day)
    return archive

@app.get("/api/cache", dependencies=[Depends(validate_api_key)])
async def get_cache_info():
    return {
        "cached_dates": list(scraper.cache.keys()),
        "count": len(scraper.cache)
    }

@app.get("/api/files", dependencies=[Depends(validate_api_key)])
async def get_files_info():
    data_dir = Path("./data")
    if not data_dir.exists():
        return {"files": [], "count": 0}
    
    files = sorted([f.stem for f in data_dir.glob("*.json")])
    return {"files": files, "count": len(files)}


@app.delete("/api/clear", dependencies=[Depends(validate_api_key)])
async def clear_all_files():
    data_dir = Path("./data")
    if not data_dir.exists():
        return {"message": "No data directory"}

    deleted_files = []
    errors = []

    for file in data_dir.glob("*.json"):
        try:
            file.unlink()
            deleted_files.append(file.name)
        except Exception as e:
            errors.append({"file": file.name, "error": str(e)})

    return {
        "deleted_files": deleted_files,
        "count": len(deleted_files),
        "errors": errors
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860, timeout_keep_alive=120)