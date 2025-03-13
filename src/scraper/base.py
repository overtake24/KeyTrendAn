import aiohttp
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, source_config):
        self.config = source_config
        self.session = None

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def init_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    @abstractmethod
    async def scrape(self, keywords, limit=10):
        pass

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None