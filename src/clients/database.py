import asyncpg
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 7432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "fastapi_project"
    min_size: int = 2
    max_size: int = 10


class Database:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig()
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            min_size=self.config.min_size,
            max_size=self.config.max_size,
        )

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized. Call .connect() first.")
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        async with self.connection() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args) -> str:
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        async with self.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        async with self.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> object | None:
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)


db = Database()
