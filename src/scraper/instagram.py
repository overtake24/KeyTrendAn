import aiohttp
import json
import random
import os
from dotenv import load_dotenv
from .base import BaseScraper

# .env dosyasını yükle
load_dotenv()


class InstagramScraper(BaseScraper):
    async def scrape(self, keywords, limit=10):
        await self.init_session()
        results = []

        # Instagram API için kimlik bilgileri
        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        business_id = os.getenv("INSTAGRAM_BUSINESS_ID")

        # Her zamanki gibi API anahtarı yoksa örnek veri dön
        if not access_token or not business_id:
            for keyword in keywords:
                hashtag = keyword.replace(" ", "")

                # Örnek Instagram verileri
                posts = []
                for i in range(limit):
                    posts.append({
                        "id": f"post_{i}_{hashtag}",
                        "type": random.choice(["image", "video", "carousel"]),
                        "likes_count": random.randint(10, 1000),
                        "comments_count": random.randint(0, 100),
                        "caption": f"Örnek post {i} ile #{hashtag} hashtagi",
                        "created_time": f"2023-01-0{i + 1}T12:00:00Z"
                    })

                results.append({
                    "keyword": keyword,
                    "source": "instagram",
                    "data": posts
                })

            return results

        # Gerçek API için (Meta Graph API)
        try:
            for keyword in keywords:
                hashtag = keyword.replace(" ", "")

                # Not: Gerçek Instagram API'si hashtag araması için farklı adımlar gerektirir
                # ve iş hesabınızın buna yetkisi olması gerekir
                # Şimdilik örnek verileri döndürüyoruz

                posts = []
                for i in range(limit):
                    posts.append({
                        "id": f"post_{i}_{hashtag}",
                        "type": random.choice(["image", "video", "carousel"]),
                        "likes_count": random.randint(10, 1000),
                        "comments_count": random.randint(0, 100),
                        "caption": f"Örnek post {i} ile #{hashtag} hashtagi",
                        "created_time": f"2023-01-0{i + 1}T12:00:00Z"
                    })

                results.append({
                    "keyword": keyword,
                    "source": "instagram",
                    "data": posts
                })

        except Exception as e:
            for keyword in keywords:
                results.append({
                    "keyword": keyword,
                    "source": "instagram",
                    "error": str(e)
                })

        return results