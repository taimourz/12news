import asyncio
import random
import pytz
from datetime import datetime, timedelta
from typing import Dict
from app.services.browser import BrowserManager
from app.services.parser import HTMLParser
from app.repositories.archive_repo import ArchiveRepository
from app.models.archive import DayArchive
from app.config import settings

PKT = pytz.timezone("Asia/Karachi")

class ScraperService:
    def __init__(
        self,
        browser_manager: BrowserManager,
        parser: HTMLParser,
        repository: ArchiveRepository
    ):
        self.browser = browser_manager
        self.parser = parser
        self.repository = repository
        self.base_url = settings.BASE_URL
        self.cache: Dict[str, DayArchive] = {}
    
    def get_todays_date(self) -> str:
        now = datetime.now(PKT)
        past = now.replace(year=now.year - 12)
        return past.strftime('%Y-%m-%d')

    def get_tomorrows_date(self) -> str:
        today_str = self.get_todays_date()
        today_dt = datetime.strptime(today_str, '%Y-%m-%d')
        tomorrow_dt = today_dt + timedelta(days=1)        
        return tomorrow_dt.strftime('%Y-%m-%d')
    
    async def fetch_page(self, url: str, retry_count: int = 0) -> str:
        max_retries = settings.MAX_RETRIES
        
        context = await self.browser.create_stealth_context()
        page = await context.new_page()

        print(f"  Fetching: {url} (attempt {retry_count + 1}/{max_retries + 1})")
        
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            response = await page.goto(
                url, 
                wait_until="domcontentloaded",
                timeout=settings.TIMEOUT
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
                print(f"  ✓ Content loaded successfully")
            except Exception as wait_err:
                print(f"  ⚠ Timeout waiting for content: {wait_err}")
            
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
            
            print(f"  HTML length: {len(html)} characters")
            
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
    
    async def scrape_day(self, date_string: str) -> DayArchive:
            
        sections = [
            'front-page', 'national', 'business', 'international',
            'sport', 'editorial', 'back-page', 'other-voices',
            'letters', 'books-authors', 'business-finance',
            'young-world', 'sunday-magzine', 'icon'
        ]
        
        day_archive = DayArchive(
            date=date_string,
            sections={},
            cached_at=datetime.now().isoformat()
        )

        await self.browser.init_browser()

        for section in sections:
            print(f"Scraping {section} for {date_string}...")
            try:
                url = f"{self.base_url}/{section}/{date_string}"
                html = await self.fetch_page(url)
                articles = self.parser.parse_section(html, section, date_string)

                day_archive.sections[section] = articles
                print(f"   Found {len(articles)} articles in {section}")

                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as err:
                print(f"✗ Failed to scrape {section}: {err}")
                day_archive.sections[section] = []

        await self.repository.save(day_archive)
        self.cache[date_string] = day_archive

        return day_archive
    
    async def load_archive(self, date_string: str) -> DayArchive | None:
        if date_string in self.cache:
            return self.cache[date_string]
        
        archive = await self.repository.load(date_string)
        if archive:
            self.cache[date_string] = archive
        return archive
    
    async def ensure_tomorrow_exists(self):
        tomorrow = self.get_tomorrows_date()
        
        if await self.repository.file_exists(tomorrow):
            print(f"Tomorrow's data already exists: {tomorrow}")
            return
        
        print(f"Precomputing tomorrow's data: {tomorrow}")
        try:
            await self.scrape_day(tomorrow)
        except Exception as e:
            print(f"Error precomputing tomorrow: {e}")