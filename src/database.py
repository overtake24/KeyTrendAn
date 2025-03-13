import aiosqlite
import json
import asyncio


class Database:
    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def init(self):
        self.db = await aiosqlite.connect("keyword_trends.db")
        await self._create_tables()

    async def _create_tables(self):
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS keyword_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche TEXT,
            keyword TEXT,
            source TEXT,
            data TEXT,
            region TEXT,
            city TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS data_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            source_name TEXT,
            source_url TEXT,
            source_type TEXT,
            auth_type TEXT,
            auth_credentials TEXT,
            scrape_method TEXT,
            extra_params TEXT
        )
        """)
        await self.db.commit()

    async def save_trends(self, niche, keyword, source, data, region=None, city=None):
        await self.db.execute(
            """INSERT INTO keyword_trends (niche, keyword, source, data, region, city) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (niche, keyword, source, json.dumps(data), region, city)
        )
        await self.db.commit()

    async def get_trends(self, niche=None, keyword=None, days=7):
        query = "SELECT keyword, source, data, timestamp FROM keyword_trends WHERE 1=1"
        params = []

        if niche:
            query += " AND niche = ?"
            params.append(niche)

        if keyword:
            query += " AND keyword LIKE ?"
            params.append(f"%{keyword}%")

        query += " AND timestamp >= datetime('now', '-' || ? || ' days')"
        params.append(days)

        query += " ORDER BY timestamp DESC"

        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "keyword": row[0],
                    "source": row[1],
                    "data": json.loads(row[2]),
                    "timestamp": row[3]
                }
                for row in rows
            ]

    async def add_source(self, category, name, url, source_type="api", auth_type=None,
                         auth_credentials=None, scrape_method="simple"):
        await self.db.execute(
            """INSERT INTO data_sources 
               (category, source_name, source_url, source_type, auth_type, auth_credentials, scrape_method) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (category, name, url, source_type, auth_type,
             json.dumps(auth_credentials) if auth_credentials else None, scrape_method)
        )
        await self.db.commit()

    async def get_sources_by_category(self, category):
        async with self.db.execute(
                """SELECT source_name, source_url, source_type, auth_type, auth_credentials, scrape_method 
                   FROM data_sources WHERE category = ?""",
                (category,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "name": row[0],
                    "url": row[1],
                    "type": row[2],
                    "auth_type": row[3],
                    "auth_credentials": json.loads(row[4]) if row[4] else None,
                    "scrape_method": row[5]
                }
                for row in rows
            ]

    async def close(self):
        await self.db.close()