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
        # Kullanıcı tanımlı kaynaklar için özel bir scraper sınıfı gerekiyor
        # BaseScraper soyut bir sınıf olduğu için doğrudan örneği oluşturulamaz
        # Geçici çözüm olarak TwitterScraper kullanabiliriz
        return TwitterScraper(source_config)