# src/scraper/playwright/base.py içindeki değişiklikler

from playwright.async_api import async_playwright
import aiohttp
import json
import logging
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PlaywrightBaseScraper(ABC):
    def __init__(self, source_config):
        self.config = source_config
        self.session = None
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.wait_selector = source_config.get("extra_params", {}).get("wait_selector", "body")
        self.timeout = source_config.get("extra_params", {}).get("timeout", 60000)  # 60 saniye (artırıldı)
        # Farklı user-agent'lar
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.user_agent = random.choice(self.user_agents)
        self.headless = False  # Görünür mod aktif edildi

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def init_session(self):
        """Playwright ve HTTP oturumlarını başlat"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,  # Görünür mod
                args=[
                    '--disable-blink-features=AutomationControlled',  # Automation algılamasını devre dışı bırak
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
                bypass_csp=True,  # Content Security Policy bypass
                ignore_https_errors=True,
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
                }
            )

            # Bot algılamasını atlatmak için navigator.webdriver'ı sahte bir değerle değiştir
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });

                // Chrome detectionlarını bypass et
                window.chrome = {
                    runtime: {},
                };

                // Navigator parametrelerini ekleme
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['tr-TR', 'tr', 'en-US', 'en'],
                });

                // Automation flags'i gizle
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ],
                });
            """)

            self.page = await self.context.new_page()

            # Hata yakalama
            await self.page.add_init_script("""
                window.addEventListener('error', (event) => {
                    console.error('Page JavaScript error:', event.message, event.error);
                });
            """)

    @abstractmethod
    async def scrape(self, keywords, limit=10):
        """Her scraper tarafından uygulanacak ana scraping metodu"""
        pass

    async def navigate(self, url, wait_selector=None, timeout=None):
        """Bir URL'ye git ve belirli bir seçicinin yüklenmesini bekle"""
        try:
            # İnsan benzeri gecikme ekle
            await self.page.wait_for_timeout(random.randint(1000, 3000))

            # Sayfaya git
            response = await self.page.goto(
                url,
                timeout=timeout or self.timeout,
                wait_until="domcontentloaded"  # Değiştirildi: networkidle yerine domcontentloaded
            )

            # Sayfanın tamamen yüklenmesi için ek bekleme
            await self.page.wait_for_timeout(random.randint(2000, 5000))

            # İnsan benzeri davranış - rastgele sayfa kaydırma
            await self.page.evaluate("""
                const scrollHeight = Math.floor(Math.random() * 500);
                window.scrollBy(0, scrollHeight);
            """)

            await self.page.wait_for_timeout(random.randint(500, 1500))

            # Seçici için bekle
            if wait_selector or self.wait_selector:
                try:
                    await self.page.wait_for_selector(
                        wait_selector or self.wait_selector,
                        state="visible",
                        timeout=timeout or self.timeout
                    )
                except Exception as e:
                    logger.warning(
                        f"Selector not found: {wait_selector or self.wait_selector}, but continuing. {str(e)}")
                    # Ekran görüntüsü al
                    screenshot = await self.take_screenshot()
                    logger.debug(f"Current page content when selector not found: {await self.page.content()[:1000]}")

            # İnsan benzeri davranış - sayfada biraz daha bekle
            await self.page.wait_for_timeout(random.randint(1000, 3000))

            return response
        except Exception as e:
            logger.error(f"Navigation error to {url}: {str(e)}")
            # Ekran görüntüsü al
            screenshot = await self.take_screenshot()
            return None

    async def extract_text(self, selector, multiple=False):
        """Seçiciden metin içeriği çıkar"""
        try:
            # İnsan benzeri gecikme
            await self.page.wait_for_timeout(random.randint(500, 1500))

            if multiple:
                elements = await self.page.query_selector_all(selector)
                return [await element.text_content() for element in elements]
            else:
                element = await self.page.query_selector(selector)
                if element:
                    return await element.text_content()
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {selector}: {str(e)}")
            return None if not multiple else []

    async def extract_attribute(self, selector, attribute, multiple=False):
        """Seçiciden bir özniteliği çıkar"""
        try:
            # İnsan benzeri gecikme
            await self.page.wait_for_timeout(random.randint(500, 1500))

            if multiple:
                elements = await self.page.query_selector_all(selector)
                return [await element.get_attribute(attribute) for element in elements]
            else:
                element = await self.page.query_selector(selector)
                if element:
                    return await element.get_attribute(attribute)
                return None
        except Exception as e:
            logger.error(f"Error extracting attribute {attribute} from {selector}: {str(e)}")
            return None if not multiple else []

    async def evaluate(self, script, arg=None):
        """Sayfada JavaScript çalıştır"""
        try:
            # İnsan benzeri gecikme
            await self.page.wait_for_timeout(random.randint(500, 1500))

            return await self.page.evaluate(script, arg)
        except Exception as e:
            logger.error(f"Error evaluating script: {str(e)}")
            return None

    async def take_screenshot(self, path=None):
        """Hata ayıklama için ekran görüntüsü al"""
        try:
            if path:
                await self.page.screenshot(path=path)
            else:
                return await self.page.screenshot()
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None

    async def close(self):
        """Kaynakları temizle"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            if self.session:
                await self.session.close()
                self.session = None
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")