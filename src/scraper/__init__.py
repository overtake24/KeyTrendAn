from .base import BaseScraper
from .google import GoogleTrendsScraper
from .twitter import TwitterScraper


def get_scraper(source_config):
    source_type = source_config.get("name", "").lower()

    if source_type == "google_trends":
        return GoogleTrendsScraper(source_config)
    elif source_type == "twitter":
        return TwitterScraper(source_config)
    else:
        # Kullanıcı tanımlı kaynak için basit scraper
        return BaseScraper(source_config)