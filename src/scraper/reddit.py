import aiohttp
import json
import base64
import os
from dotenv import load_dotenv
from .base import BaseScraper

# .env dosyasını yükle
load_dotenv()


class RedditScraper(BaseScraper):
    async def scrape(self, keywords, limit=10):
        await self.init_session()
        results = []

        # Reddit API için kimlik bilgileri
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        username = os.getenv("REDDIT_USERNAME")
        password = os.getenv("REDDIT_PASSWORD")

        # Örnek veriler için
        if not client_id or client_id == "YOUR_CLIENT_ID":
            for keyword in keywords:
                # Mock veri oluştur
                posts = []
                for i in range(5):
                    posts.append({
                        "title": f"Reddit: {keyword} hakkında örnek post {i}",
                        "score": 10 * (i + 1),
                        "comments": 5 * (i + 1),
                        "url": f"https://reddit.com/r/example/post{i}",
                        "created_utc": f"2023-01-0{i + 1}T12:00:00Z"
                    })

                results.append({
                    "keyword": keyword,
                    "source": "reddit",
                    "data": posts
                })
            return results

        # Gerçek API için
        try:
            # Reddit OAuth token al
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "User-Agent": "KeywordTrendAnalyzer/0.1 by " + username
            }

            data = {
                "grant_type": "password",
                "username": username,
                "password": password
            }

            async with self.session.post(
                    "https://www.reddit.com/api/v1/access_token",
                    headers=headers,
                    data=data
            ) as response:
                token_data = await response.json()
                access_token = token_data.get("access_token")

                if not access_token:
                    raise Exception("Reddit token alınamadı")

                # Token ile arama yap
                headers = {
                    "Authorization": f"bearer {access_token}",
                    "User-Agent": "KeywordTrendAnalyzer/0.1 by " + username
                }

                for keyword in keywords:
                    search_url = f"https://oauth.reddit.com/search?q={keyword}&sort=relevance&limit={limit}"

                    async with self.session.get(search_url, headers=headers) as search_response:
                        search_data = await search_response.json()

                        posts = []
                        for post in search_data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})
                            posts.append({
                                "title": post_data.get("title"),
                                "score": post_data.get("score"),
                                "comments": post_data.get("num_comments"),
                                "url": post_data.get("url"),
                                "created_utc": post_data.get("created_utc")
                            })

                        results.append({
                            "keyword": keyword,
                            "source": "reddit",
                            "data": posts
                        })

        except Exception as e:
            for keyword in keywords:
                results.append({
                    "keyword": keyword,
                    "source": "reddit",
                    "error": str(e)
                })

        return results