from app.services.scraper import ScraperService
from app.services.browser import BrowserManager
from app.services.parser import HTMLParser
from app.repositories.archive_repo import ArchiveRepository

_browser_manager: BrowserManager | None = None
_scraper_service: ScraperService | None = None

async def get_browser_manager() -> BrowserManager:
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager

async def get_scraper_service() -> ScraperService:
    global _scraper_service
    if _scraper_service is None:
        browser = await get_browser_manager()
        parser = HTMLParser()
        repository = ArchiveRepository()
        _scraper_service = ScraperService(browser, parser, repository)
    return _scraper_service