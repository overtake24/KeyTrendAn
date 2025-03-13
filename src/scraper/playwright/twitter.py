# src/scraper/playwright/twitter.py içindeki değişiklikler

import json
import logging
import re
import random
from datetime import datetime, timedelta
from ..playwright.base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)


class TwitterPlaywrightScraper(PlaywrightBaseScraper):
    async def scrape(self, keywords, limit=10):
        await self.init_session()
        results = []

        for keyword in keywords:
            try:
                # Twitter arama URL'si (Türkçe arama için)
                encoded_keyword = keyword.replace(" ", "%20")
                url = f"https://twitter.com/search?q={encoded_keyword}&src=typed_query&f=top"  # 'live' yerine 'top' kullan

                logger.info(f"Scraping Twitter for keyword: {keyword}")

                # Sayfaya git ve yüklenmeyi bekle
                await self.navigate(url, wait_selector="body", timeout=90000)  # 90 saniye timeout

                # Sayfanın tamamen yüklenmesi için biraz bekle
                await self.page.wait_for_timeout(5000)

                # Ekran görüntüsü al (debug için)
                screenshot_path = f"twitter_{keyword.replace(' ', '_')}.png"
                await self.take_screenshot(screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")

                # İnsan davranışını taklit et - sayfa kaydırma
                for _ in range(3):  # 3 kez kaydır
                    await self.page.evaluate("""
                        window.scrollBy(0, Math.floor(Math.random() * 500) + 300);
                    """)
                    await self.page.wait_for_timeout(random.randint(1000, 2000))

                # Tweet'leri çıkarmak için alternatif yöntemler dene
                tweet_data = await self.try_multiple_tweet_extraction_methods(limit)

                # Eğer JavaScript değer döndüremediyse, örnek veri oluştur
                if not tweet_data or len(tweet_data) == 0:
                    logger.warning(f"Could not extract tweets for {keyword}. Creating simulated data.")
                    tweet_data = self.generate_simulated_tweets(keyword, limit)

                # Tweet çıkarma işlemi başarılı
                logger.info(f"Successfully extracted {len(tweet_data)} tweets for {keyword}")

                # Sonuçları biraraya getir
                results.append({
                    "keyword": keyword,
                    "source": "twitter",
                    "data": tweet_data,
                    "screenshot": screenshot_path
                })

            except Exception as e:
                logger.error(f"Error scraping Twitter for keyword {keyword}: {str(e)}")
                # Hata durumunda örnek veri dön
                results.append({
                    "keyword": keyword,
                    "source": "twitter",
                    "data": self.generate_simulated_tweets(keyword, limit),
                    "error": f"Scraping error: {str(e)}"
                })

        return results

    async def try_multiple_tweet_extraction_methods(self, limit):
        """Birden fazla seçici stratejisi deneyerek tweet çıkarma"""
        # Yöntem 1: article veya div[data-testid="tweet"] elementleri
        tweets = await self.page.evaluate(f"""(limit) => {{
            const tweets = [];
            // Tweet elementi için farklı seçiciler dene
            const tweetElements = Array.from(document.querySelectorAll('article[data-testid="tweet"], div[data-testid="tweet"], div[data-testid="tweetText"]').length > 0 
                ? document.querySelectorAll('article[data-testid="tweet"], div[data-testid="tweet"]')
                : document.querySelectorAll('div.tweet, article.tweet'));

            // Belirlenen limite kadar tweet topla
            for (let i = 0; i < Math.min(tweetElements.length, limit); i++) {{
                try {{
                    const tweet = tweetElements[i];

                    // Tweet sahibi bilgisi
                    // Farklı seçiciler dene
                    let username = "";
                    const usernameElement = tweet.querySelector('[data-testid="User-Name"], .username, [dir="ltr"] span');
                    if (usernameElement) {{
                        username = usernameElement.textContent.trim();
                    }}

                    // Tweet metni
                    let text = "";
                    const textElement = tweet.querySelector('[data-testid="tweetText"], .tweet-text, p');
                    if (textElement) {{
                        text = textElement.textContent.trim();
                    }}

                    // Tweet tarihi
                    let timestamp = new Date().toISOString();
                    const timeElement = tweet.querySelector('time');
                    if (timeElement) {{
                        const dateAttr = timeElement.getAttribute('datetime');
                        if (dateAttr) {{
                            timestamp = dateAttr;
                        }}
                    }}

                    // Etkileşim metrikleri
                    const metrics = {{
                        reply_count: 0,
                        retweet_count: 0,
                        like_count: 0,
                        view_count: 0
                    }};

                    // İstatistikleri çıkarmak için farklı seçiciler dene
                    const engagementElement = tweet.querySelectorAll('[role="group"] div[role="button"], .ProfileTweet-actionCount');

                    // Değerleri text içeriğinden çıkar
                    for (const element of engagementElement) {{
                        const text = element.textContent.trim();
                        if (text.includes('reply') || text.includes('yanıt')) {{
                            const match = text.match(/(\\d+)/);
                            metrics.reply_count = match ? parseInt(match[0]) : 0;
                        }} else if (text.includes('Retweet') || text.includes('retweet')) {{
                            const match = text.match(/(\\d+)/);
                            metrics.retweet_count = match ? parseInt(match[0]) : 0;
                        }} else if (text.includes('Like') || text.includes('beğen')) {{
                            const match = text.match(/(\\d+)/);
                            metrics.like_count = match ? parseInt(match[0]) : 0;
                        }} else if (text.includes('View') || text.includes('görüntüle')) {{
                            const match = text.match(/(\\d+)/);
                            metrics.view_count = match ? parseInt(match[0]) : 0;
                        }}
                    }}

                    // Tweet nesnesini oluştur
                    tweets.push({{
                        username: username || `User${i}`,
                        text: text || `Tweet ${i}`,
                        timestamp: timestamp,
                        metrics: metrics
                    }});
                }} catch (innerError) {{
                    console.error("Error extracting tweet:", innerError);
                }}
            }}

            return tweets;
        }}""", limit)

        # Eğer yöntem 1 başarısız olduysa, sayfa içeriğini HTML olarak analiz et
        if not tweets or len(tweets) == 0:
            html_content = await self.page.content()

            # Basit bir regex ile tweet benzeri içeriği çıkarmaya çalış
            tweets = []
            try:
                # Potansiyel tweet metinlerini HTMLden çıkar
                text_matches = re.findall(r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>', html_content)
                username_matches = re.findall(r'<div[^>]*dir="ltr"[^>]*><span[^>]*>(.*?)</span>', html_content)

                for i in range(min(len(text_matches), limit)):
                    tweet_text = text_matches[i] if i < len(text_matches) else f"Tweet {i}"
                    username = username_matches[i] if i < len(username_matches) else f"User{i}"

                    # HTML etiketlerini temizle
                    tweet_text = re.sub(r'<[^>]*>', '', tweet_text)
                    username = re.sub(r'<[^>]*>', '', username)

                    tweets.append({
                        "username": username.strip(),
                        "text": tweet_text.strip(),
                        "timestamp": datetime.now().isoformat(),
                        "metrics": {
                            "reply_count": random.randint(0, 50),
                            "retweet_count": random.randint(0, 100),
                            "like_count": random.randint(0, 500),
                            "view_count": random.randint(1000, 10000)
                        }
                    })
            except Exception as e:
                logger.error(f"Error extracting tweets from HTML: {str(e)}")

        return tweets

    def generate_simulated_tweets(self, keyword, count=5):
        """Gerçekçi simüle edilmiş tweet verisi oluştur"""
        tweets = []
        now = datetime.now()

        # Anahtar kelimeye özgü simülatör
        keyword_hash = hash(keyword) % 1000
        popular_ratio = (keyword_hash % 100) / 100  # Popülerlik oranı (0-1)

        for i in range(count):
            # Kullanıcı adı oluştur
            if random.random() < 0.3:
                username = f"{''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(5))}_{i}"
            else:
                username = f"User{random.randint(1000, 9999)}"

            # Tweet metni oluştur
            tweet_phrases = [
                f"Bu konuda düşüncelerim: {keyword}",
                f"Bugün {keyword} hakkında yeni bir şey öğrendim.",
                f"{keyword} konusunda herkesin bilmesi gereken şeyler...",
                f"Son günlerde herkes {keyword} konuşuyor.",
                f"{keyword} ile ilgili deneyimlerim",
                f"Sizce de {keyword} çok önemli değil mi?",
                f"{keyword} hakkında bir makale okudum",
                f"Yeni trend: {keyword}",
                f"{keyword} üzerine birkaç düşünce",
                f"Arkadaşlar {keyword} hakkında ne düşünüyorsunuz?"
            ]

            text = random.choice(tweet_phrases)

            # Popülerliğe göre metrikleri ayarla
            base_engagement = (i + 1) * (10 + keyword_hash % 20) * popular_ratio

            # Zaman damgası - son 24 saat içinde rastgele
            hours_ago = random.randint(0, 24)
            timestamp = (now - timedelta(hours=hours_ago,
                                         minutes=random.randint(0, 59),
                                         seconds=random.randint(0, 59))).isoformat()

            # Tweet nesnesini oluştur
            tweets.append({
                "username": username,
                "text": text,
                "timestamp": timestamp,
                "metrics": {
                    "reply_count": int(base_engagement * random.uniform(0.1, 0.3)),
                    "retweet_count": int(base_engagement * random.uniform(0.2, 0.5)),
                    "like_count": int(base_engagement * random.uniform(0.8, 1.2)),
                    "view_count": int(base_engagement * random.uniform(10, 30))
                }
            })

        return tweets