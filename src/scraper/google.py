import aiohttp
import json
from pytrends.request import TrendReq
import pandas as pd
import asyncio
from .base import BaseScraper


class GoogleTrendsScraper(BaseScraper):
    async def scrape(self, keywords, limit=10):
        results = []

        # Google Trends için eş zamanlı olmayan bir yaklaşım kullanıyoruz
        # pytrends kütüphanesi doğrudan asenkron değil
        for keyword in keywords:
            # Senkron kodu asyncio.to_thread ile çalıştırıyoruz
            data = await asyncio.to_thread(self._get_trend_data, keyword)

            results.append({
                "keyword": keyword,
                "source": "google_trends",
                "data": data
            })

        return results

    def _get_trend_data(self, keyword):
        # Google Trends API'si için pytrends
        pytrends = TrendReq(hl='tr-TR', tz=180)
        pytrends.build_payload([keyword], cat=0, timeframe='today 3-m')

        try:
            interest_over_time_df = pytrends.interest_over_time()

            if not interest_over_time_df.empty:
                # DataFrame'i dictionary'e çeviriyoruz
                return interest_over_time_df[keyword].to_dict()
            else:
                return {"error": "No data found for this keyword"}
        except Exception as e:
            return {"error": str(e)}