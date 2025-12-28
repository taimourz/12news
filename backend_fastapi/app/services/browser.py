import re
from playwright.async_api import async_playwright, Browser, BrowserContext
from app.config import settings
from app.services.fingerprint import FingerprintGenerator

class BrowserManager:
    def __init__(self):
        self.browser: Browser | None = None
        self.playwright = None
        self.proxy_url = settings.PROXY_URL 
    
    async def init_browser(self) -> Browser:
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.HEADLESS,
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

            print(f"  Using proxy server: {server}")
            print(f"  Using proxy username: {username}")

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
            // Overwrite webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Remove automation indicators
            delete navigator.__proto__.webdriver;
            
            // Mock plugins
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
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            
            // Mock hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            
            // Mock device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            // Mock chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Randomize canvas fingerprint
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const dataURL = originalToDataURL.apply(this, arguments);
                // Add subtle noise to prevent canvas fingerprinting
                return dataURL;
            };
            
            // Override WebGL fingerprinting
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
            
            // Mock battery API
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0
                })
            });
            
            // Remove Playwright-specific properties
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
            
            // Console.debug to hide
            const originalDebug = console.debug;
            console.debug = function() {
                if (arguments[0] && arguments[0].includes('Playwright')) {
                    return;
                }
                return originalDebug.apply(console, arguments);
            };
        """)
        
        return context
    
    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None