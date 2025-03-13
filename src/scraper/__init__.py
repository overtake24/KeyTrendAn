# src/scraper/__init__.py

from .base import BaseScraper
from .google import GoogleTrendsScraper
from .twitter import TwitterScraper
from .reddit import RedditScraper
from .hackernews import HackerNewsScraper
from .instagram import InstagramScraper
from .youtube import YouTubeScraper
from .news import NewsScraper
from .pinterest import PinterestScraper
from .linkedin import LinkedInScraper
from .amazon import AmazonScraper
from .ebay import EbayScraper
from .otto import OttoScraper

# Playwright implementasyonları - doğru import yolları
from .playwright.base import PlaywrightBaseScraper
from .playwright.google import GoogleTrendsPlaywrightScraper
from .playwright.twitter import TwitterPlaywrightScraper


def get_scraper(source_config):
    source_type = source_config.get("name", "").lower()
    scrape_method = source_config.get("scrape_method", "playwright").lower()

    # Playwright tabanlı scraperlar (varsayılan)
    if scrape_method == "playwright":
        if source_type == "google_trends":
            return GoogleTrendsPlaywrightScraper(source_config)
        elif source_type == "twitter":
            return TwitterPlaywrightScraper(source_config)
        # Diğer Playwright scraperlar eklendikçe buraya eklenecek
        else:
            # Varsayılan olarak Twitter playwright scraper kullanın
            # Diğer scraperlar eklendikçe kademeli olarak genişletin
            return TwitterPlaywrightScraper(source_config)

    # API tabanlı scraperlar
    elif scrape_method == "api":
        if source_type == "google_trends":
            return GoogleTrendsScraper(source_config)
        elif source_type == "twitter":
            return TwitterScraper(source_config)
        elif source_type == "reddit":
            return RedditScraper(source_config)
        elif source_type == "hackernews":
            return HackerNewsScraper(source_config)
        elif source_type == "instagram":
            return InstagramScraper(source_config)
        elif source_type == "youtube":
            return YouTubeScraper(source_config)
        elif source_type == "news":
            return NewsScraper(source_config)
        elif source_type == "pinterest":
            return PinterestScraper(source_config)
        elif source_type == "linkedin":
            return LinkedInScraper(source_config)
        elif source_type == "amazon":
            return AmazonScraper(source_config)
        elif source_type == "ebay":
            return EbayScraper(source_config)
        elif source_type == "otto":
            return OttoScraper(source_config)
        else:
            # Varsayılan olarak Twitter scraper kullanın
            return TwitterScraper(source_config)

    # Mock veri için API scraperlarını kullanın
    else:  # mock veya diğer seçenekler
        if source_type == "google_trends":
            return GoogleTrendsScraper(source_config)
        elif source_type == "twitter":
            return TwitterScraper(source_config)
        elif source_type == "reddit":
            return RedditScraper(source_config)
        elif source_type == "hackernews":
            return HackerNewsScraper(source_config)
        elif source_type == "instagram":
            return InstagramScraper(source_config)
        elif source_type == "youtube":
            return YouTubeScraper(source_config)
        elif source_type == "news":
            return NewsScraper(source_config)
        elif source_type == "pinterest":
            return PinterestScraper(source_config)
        elif source_type == "linkedin":
            return LinkedInScraper(source_config)
        elif source_type == "amazon":
            return AmazonScraper(source_config)
        elif source_type == "ebay":
            return EbayScraper(source_config)
        elif source_type == "otto":
            return OttoScraper(source_config)
        else:
            # Varsayılan olarak Twitter scraper kullanın
            return TwitterScraper(source_config)