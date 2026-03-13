import asyncpg

from app.config import settings

db_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global db_pool

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to your .env file.")

    db_pool = await asyncpg.create_pool(settings.database_url)


async def close_db() -> None:
    global db_pool

    if db_pool is not None:
        await db_pool.close()
        db_pool = None


def get_db_pool() -> asyncpg.Pool:
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return db_pool
