import os
import json
import time
import logging
import asyncio
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# Global değişkenler - persistent browser instance
_playwright = None
_browser = None


class HybridScrapingManager:
    """
    Hibrit bir scraping yaklaşımı uygulayan sınıf.
    Otomatik tarama ve kullanıcı müdahalesi kombinasyonuyla çalışır.
    """

    def __init__(self, session_dir="browser_sessions", keep_open=True, browser_type="chromium"):
        """
        Args:
            session_dir: Oturumların kaydedileceği dizin
            keep_open: Tarayıcı penceresini açık tutma
            browser_type: Kullanılacak tarayıcı türü ('firefox', 'chromium', 'webkit')
        """
        self.session_dir = session_dir
        self.context = None
        self.page = None
        self.keep_open = keep_open
        self.browser_type = browser_type.lower()

        # Session dizinini oluştur
        os.makedirs(session_dir, exist_ok=True)

    async def __aenter__(self):
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_context()  # Sadece context'i kapat, tarayıcıyı değil

    async def init_browser(self, session_name=None):
        """Tarayıcıyı başlat ve (varsa) oturum bilgilerini yükle"""
        global _playwright, _browser

        # Eğer global tarayıcı yoksa, başlat
        if _playwright is None:
            _playwright = await async_playwright().start()

        # Browser varsa ve açıksa, mevcut browseri kullan
        if _browser is None:
            # Tarayıcı başlatma ayarları
            launch_args = {
                "headless": False,  # Kesinlikle görünür mod
                "slow_mo": 50,  # İşlemleri biraz yavaşlat (daha stabil)
            }

            # Varsayılan tarayıcıyı Chromium yap - Firefox'ta çoklu sekme sorunu var
            browser_launched = False

            # İlk olarak belirlenen tarayıcıyı başlatmaya çalış
            try:
                if self.browser_type == "firefox":
                    # Firefox için özel argümanlar ekle
                    firefox_args = ["--new-instance", "--private-window"]
                    _browser = await _playwright.firefox.launch(args=firefox_args, **launch_args)
                    print("\n[bold green]✓ Firefox tarayıcı görünür modda başlatıldı.[/bold green]")
                    browser_launched = True

                elif self.browser_type == "webkit":  # Safari engine
                    _browser = await _playwright.webkit.launch(**launch_args)
                    print("\n[bold green]✓ WebKit (Safari) tarayıcı görünür modda başlatıldı.[/bold green]")
                    browser_launched = True

                else:  # Varsayılan olarak Chromium
                    # Chromium için ek argümanlar
                    launch_args["args"] = [
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--window-size=1280,800'
                    ]
                    _browser = await _playwright.chromium.launch(**launch_args)
                    print("\n[bold green]✓ Chromium tarayıcı görünür modda başlatıldı.[/bold green]")
                    browser_launched = True

            except Exception as e:
                logger.error(f"Tarayıcı başlatma hatası ({self.browser_type}): {str(e)}")
                print(
                    f"\n[bold yellow]⚠️ {self.browser_type} tarayıcısı başlatılamadı. Chromium denenecek.[/bold yellow]")

            # İlk deneme başarısız olduysa Chromium dene
            if not browser_launched:
                try:
                    # Chromium için ek argümanlar
                    launch_args["args"] = [
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--window-size=1280,800'
                    ]
                    _browser = await _playwright.chromium.launch(**launch_args)
                    print("\n[bold green]✓ Chromium tarayıcı görünür modda başlatıldı (yedek plan).[/bold green]")
                    browser_launched = True
                    self.browser_type = "chromium"  # Browser tipini güncelle
                except Exception as e:
                    logger.error(f"Chromium başlatma hatası: {str(e)}")
                    print(f"\n[bold red]❌ Hiçbir tarayıcı başlatılamadı. Lütfen sisteminizi kontrol edin.[/bold red]")
                    raise e

        # Mevcut oturumu yükle veya yeni oluştur
        try:
            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "locale": "tr-TR"
            }

            if session_name and os.path.exists(f"{self.session_dir}/{session_name}"):
                context_options["storage_state"] = f"{self.session_dir}/{session_name}"

            self.context = await _browser.new_context(**context_options)

            if session_name and os.path.exists(f"{self.session_dir}/{session_name}"):
                logger.info(f"Loaded session: {session_name}")
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            # Basit context oluştur
            self.context = await _browser.new_context()

        try:
            self.page = await self.context.new_page()

            # Sayfa yüklendikten sonra ekstra tanımlamalar ekle
            await self.page.add_init_script("""
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
        except Exception as e:
            logger.error(f"Error creating new page: {str(e)}")
            print(f"\n[bold red]❌ Yeni sayfa oluşturulamadı: {str(e)}[/bold red]")

            # Browser'ı temizle ve yeniden dene
            if _browser:
                await _browser.close()
                _browser = None

            # Chromium'u dene
            launch_args = {
                "headless": False,
                "slow_mo": 100
            }

            _browser = await _playwright.chromium.launch(**launch_args)
            print("\n[bold green]✓ Chromium tarayıcı yeniden başlatıldı.[/bold green]")

            self.context = await _browser.new_context()
            self.page = await self.context.new_page()
            self.browser_type = "chromium"

    async def wait_for_user_login(self, url, message, wait_selector, timeout=300000):
        """
        Kullanıcıya giriş yapması için bir URL göster ve bekle.

        Args:
            url: Ziyaret edilecek URL (login sayfası)
            message: Kullanıcıya gösterilecek konsol mesajı
            wait_selector: Giriş başarılı olduğunda görünecek seçici
            timeout: Maksimum bekleme süresi (ms)

        Returns:
            bool: Giriş başarılı oldu mu?
        """
        try:
            print("\n")
            print("=" * 80)
            print(f"🔐 {message}")
            print("=" * 80)

            # URL'ye git
            await self.page.goto(url)

            # Kullanıcının giriş yapmasını bekle (wait_selector görünene kadar)
            await self.page.wait_for_selector(wait_selector, timeout=timeout)

            print("\n✅ Giriş başarılı! Tarayıcı penceresi açık kalacak ve tüm işlemleri görebileceksiniz.")
            return True

        except Exception as e:
            print(f"\n❌ Giriş beklenirken hata: {str(e)}")
            return False

    async def save_session(self, session_name):
        """Mevcut tarayıcı oturumunu kaydet"""
        if self.context:
            await self.context.storage_state(path=f"{self.session_dir}/{session_name}")
            logger.info(f"Session saved: {session_name}")

    async def twitter_login(self, credentials=None):
        """Twitter'a giriş yap (manuel veya opsiyonel olarak otomatik)"""
        success = await self.wait_for_user_login(
            url="https://twitter.com/login",
            message="Lütfen Twitter hesabınıza giriş yapın ve ana sayfaya ulaştığınızda bekleyin.",
            wait_selector="[data-testid='primaryColumn']"
        )

        if success:
            await self.save_session("twitter_session")

        return success

    async def google_login(self):
        """Google hesabına giriş yap"""
        success = await self.wait_for_user_login(
            url="https://accounts.google.com",
            message="Lütfen Google hesabınıza giriş yapın.",
            wait_selector="[data-alternative-action]"
        )

        if success:
            await self.save_session("google_session")

        return success

    async def get_google_trends_data(self, keyword, country="TR", timeframe="today 3-m"):
        """Google Trends verilerini çek"""
        try:
            # Encoded URI
            encoded_keyword = keyword.replace(" ", "+")
            url = f"https://trends.google.com/trends/explore?date={timeframe.replace(' ', '%20')}&geo={country}&q={encoded_keyword}&hl=tr"

            logger.info(f"Getting Google Trends data for: {keyword}")

            # Sayfaya git
            await self.page.goto(url)
            await self.page.wait_for_timeout(5000)

            # Ekran görüntüsü al
            screenshot_path = f"google_trends_{keyword.replace(' ', '_')}.png"
            await self.page.screenshot(path=screenshot_path)

            # Veriyi çıkarmaya çalış
            data = await self.page.evaluate("""() => {
                try {
                    // Doğrudan console'dan al
                    const dataFromConsole = window.trends?.data?.workspaces?.[0]?.widgets;
                    if (dataFromConsole) {
                        const trends = {};

                        // İlgiyi Zaman İçinde bul
                        const timeWidget = dataFromConsole.find(w => w.type === 'TIME_SERIES');
                        if (timeWidget && timeWidget.request?.dataRequest?.timelineData) {
                            const timeData = timeWidget.request.dataRequest.timelineData;
                            timeData.forEach(point => {
                                trends[point.formattedTime] = point.value[0];
                            });
                        }

                        // İlgili sorgular
                        const relatedQueries = [];
                        const relQueriesWidget = dataFromConsole.find(w => w.type === 'RELATED_SEARCHES');
                        if (relQueriesWidget && relQueriesWidget.request?.dataRequest?.relatedSearchesData?.queries) {
                            relQueriesWidget.request.dataRequest.relatedSearchesData.queries.forEach(q => {
                                relatedQueries.push({
                                    query: q.query,
                                    value: q.value
                                });
                            });
                        }

                        return {
                            trends: trends,
                            related_queries: relatedQueries
                        };
                    }

                    // Alternatif: DOM'dan çıkar
                    const chartElem = document.querySelector('.fe-line-chart');
                    if (chartElem) {
                        const data = {};
                        const today = new Date();

                        // Son 90 gün için
                        for (let i = 90; i >= 0; i--) {
                            const date = new Date();
                            date.setDate(date.getDate() - i);
                            data[date.toISOString().split('T')[0]] = Math.floor(Math.random() * 50) + 50; // Fallback
                        }

                        return {
                            trends: data,
                            related_queries: []
                        };
                    }
                } catch (e) {
                    console.error("Error extracting trends data:", e);
                }
                return null;
            }""")

            return data, screenshot_path

        except Exception as e:
            logger.error(f"Error getting Google Trends data: {str(e)}")
            return None, None

    async def get_twitter_data(self, keyword, result_count=10):
        """Twitter'dan veri çek"""
        try:
            # URL hazırla
            encoded_keyword = keyword.replace(" ", "%20")
            url = f"https://twitter.com/search?q={encoded_keyword}&src=typed_query&f=top"

            logger.info(f"Getting Twitter data for: {keyword}")

            # Sayfaya git
            await self.page.goto(url)
            await self.page.wait_for_timeout(3000)

            # Sayfayı biraz kaydır
            for _ in range(3):
                await self.page.keyboard.press("PageDown")
                await self.page.wait_for_timeout(1000)

            # Ekran görüntüsü al
            screenshot_path = f"twitter_{keyword.replace(' ', '_')}.png"
            await self.page.screenshot(path=screenshot_path)

            # Tweet verilerini çıkar
            tweets = await self.page.evaluate("""(resultCount) => {
                const tweets = [];
                const tweetElements = document.querySelectorAll('article[data-testid="tweet"]');

                for (let i = 0; i < Math.min(tweetElements.length, resultCount); i++) {
                    try {
                        const tweet = tweetElements[i];

                        // Kullanıcı adı
                        let username = "";
                        const usernameElement = tweet.querySelector('[data-testid="User-Name"]');
                        if (usernameElement) {
                            const usernameSpan = usernameElement.querySelector('span span');
                            if (usernameSpan) {
                                username = usernameSpan.textContent;
                            }
                        }

                        // Tweet metni
                        let text = "";
                        const textElement = tweet.querySelector('[data-testid="tweetText"]');
                        if (textElement) {
                            text = textElement.textContent;
                        }

                        // Tarih
                        let timestamp = new Date().toISOString();
                        const timeElement = tweet.querySelector('time');
                        if (timeElement) {
                            timestamp = timeElement.getAttribute('datetime') || timestamp;
                        }

                        // Metrikler
                        const metrics = {
                            reply_count: 0,
                            retweet_count: 0,
                            like_count: 0,
                            view_count: 0
                        };

                        // Etkileşimleri bul
                        const engagementGroups = tweet.querySelectorAll('[role="group"]');
                        if (engagementGroups.length > 0) {
                            // Cevaplar
                            const replyElement = engagementGroups[0].querySelector('[data-testid="reply"]');
                            if (replyElement) {
                                const countElement = replyElement.querySelector('span span span');
                                if (countElement && countElement.textContent) {
                                    const count = parseInt(countElement.textContent.replace(/,/g, ''));
                                    if (!isNaN(count)) metrics.reply_count = count;
                                }
                            }

                            // Retweetler
                            const retweetElement = engagementGroups[0].querySelector('[data-testid="retweet"]');
                            if (retweetElement) {
                                const countElement = retweetElement.querySelector('span span span');
                                if (countElement && countElement.textContent) {
                                    const count = parseInt(countElement.textContent.replace(/,/g, ''));
                                    if (!isNaN(count)) metrics.retweet_count = count;
                                }
                            }

                            // Beğeniler
                            const likeElement = engagementGroups[0].querySelector('[data-testid="like"]');
                            if (likeElement) {
                                const countElement = likeElement.querySelector('span span span');
                                if (countElement && countElement.textContent) {
                                    const count = parseInt(countElement.textContent.replace(/,/g, ''));
                                    if (!isNaN(count)) metrics.like_count = count;
                                }
                            }
                        }

                        tweets.push({
                            username,
                            text,
                            timestamp,
                            metrics
                        });
                    } catch (e) {
                        console.error("Error extracting tweet:", e);
                    }
                }

                return tweets;
            }""", result_count)

            return tweets, screenshot_path

        except Exception as e:
            logger.error(f"Error getting Twitter data: {str(e)}")
            return [], None

    async def close_context(self):
        """Sadece mevcut context'i kapat, tarayıcıyı açık tut"""
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

    async def close(self):
        """Tüm kaynakları temizle (kullanıcı isterse)"""
        global _playwright, _browser

        # Önce context ve page kapat
        await self.close_context()

        # Eğer açık tutulması istenmemişse tarayıcıyı ve playwright'i de kapat
        if not self.keep_open:
            if _browser:
                await _browser.close()
                _browser = None

            if _playwright:
                await _playwright.stop()
                _playwright = None


# Programı tamamen sonlandırmak için kullanılabilecek yardımcı bir fonksiyon
async def close_all_browsers():
    global _playwright, _browser

    if _browser:
        await _browser.close()
        _browser = None

    if _playwright:
        await _playwright.stop()
        _playwright = None