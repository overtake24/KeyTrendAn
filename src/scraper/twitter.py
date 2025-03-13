import aiohttp
import json
import asyncio
from .base import BaseScraper


class TwitterScraper(BaseScraper):
    async def scrape(self, keywords, limit=10):
        await self.init_session()
        results = []

        # Twitter API v2 için Bearer Token
        # Gerçek projede bu token güvenli bir yerden alınmalı
        bearer_token = "YOUR_TWITTER_BEARER_TOKEN"  # Gerçek token ile değiştirin

        if not bearer_token or bearer_token == "YOUR_TWITTER_BEARER_TOKEN":
            # Gerçek token yoksa örnek veri kullan
            for keyword in keywords:
                results.append({
                    "keyword": keyword,
                    "source": "twitter",
                    "data": [f"Örnek Tweet {i} hakkında {keyword}" for i in range(5)]
                })
            return results

        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }

        for keyword in keywords:
            try:
                # Twitter API v2 endpoint
                url = f"https://api.twitter.com/2/tweets/search/recent?query={keyword}&max_results={limit}&tweet.fields=public_metrics,created_at"

                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        json_response = await response.json()

                        # API yanıtından tweet verilerini çıkar
                        tweets = []
                        if "data" in json_response:
                            for tweet in json_response["data"]:
                                tweets.append({
                                    "id": tweet["id"],
                                    "text": tweet["text"],
                                    "created_at": tweet["created_at"],
                                    "metrics": tweet.get("public_metrics", {})
                                })

                        results.append({
                            "keyword": keyword,
                            "source": "twitter",
                            "data": tweets
                        })
                    else:
                        # API hata verirse
                        error_data = await response.text()
                        results.append({
                            "keyword": keyword,
                            "source": "twitter",
                            "error": f"API Error: {response.status}",
                            "details": error_data
                        })
            except Exception as e:
                results.append({
                    "keyword": keyword,
                    "source": "twitter",
                    "error": f"Exception: {str(e)}"
                })

        return results