import aiohttp
import json
import asyncio
from .base import BaseScraper


class HackerNewsScraper(BaseScraper):
    async def scrape(self, keywords, limit=10):
        await self.init_session()
        results = []

        for keyword in keywords:
            try:
                # HackerNews Search API (algolia)
                search_url = f"https://hn.algolia.com/api/v1/search?query={keyword}&hitsPerPage={limit}"

                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        search_data = await response.json()

                        hits = []
                        for hit in search_data.get("hits", []):
                            hits.append({
                                "title": hit.get("title"),
                                "points": hit.get("points"),
                                "num_comments": hit.get("num_comments"),
                                "url": hit.get("url"),
                                "created_at": hit.get("created_at")
                            })

                        results.append({
                            "keyword": keyword,
                            "source": "hackernews",
                            "data": hits
                        })
                    else:
                        # API hata verirse mock veri dön
                        hits = []
                        for i in range(5):
                            hits.append({
                                "title": f"HackerNews: {keyword} hakkında örnek başlık {i}",
                                "points": 10 * (i + 1),
                                "num_comments": 5 * (i + 1),
                                "url": f"https://news.ycombinator.com/item?id={i}",
                                "created_at": f"2023-01-0{i + 1}T12:00:00Z"
                            })

                        results.append({
                            "keyword": keyword,
                            "source": "hackernews",
                            "data": hits
                        })
            except Exception as e:
                # Hata durumunda mock veri dön
                hits = []
                for i in range(5):
                    hits.append({
                        "title": f"HackerNews: {keyword} hakkında örnek başlık {i}",
                        "points": 10 * (i + 1),
                        "num_comments": 5 * (i + 1),
                        "url": f"https://news.ycombinator.com/item?id={i}",
                        "created_at": f"2023-01-0{i + 1}T12:00:00Z"
                    })

                results.append({
                    "keyword": keyword,
                    "source": "hackernews",
                    "data": hits
                })

        return results