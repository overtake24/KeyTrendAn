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


def get_scraper(source_config):
    source_type = source_config.get("name", "").lower()

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
        # Kullanıcı tanımlı kaynaklar için TwitterScraper kullanıyoruz
        return TwitterScraper(source_config)