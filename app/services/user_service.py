from aiogram.types import User

from app.db import get_db_pool

CREATE_BOT_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bot_users (
    telegram_user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    first_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    total_requests INTEGER NOT NULL DEFAULT 1
);
"""


UPSERT_BOT_USER_SQL = """
INSERT INTO bot_users (
    telegram_user_id,
    username,
    first_name,
    last_name,
    first_seen_at,
    last_seen_at,
    total_requests
)
VALUES ($1, $2, $3, $4, NOW(), NOW(), 1)
ON CONFLICT (telegram_user_id)
DO UPDATE SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    last_seen_at = NOW(),
    total_requests = bot_users.total_requests + 1;
"""



async def init_user_table() -> None:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(CREATE_BOT_USERS_TABLE_SQL)



async def track_user_request(user: User) -> None:
    pool = get_db_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            UPSERT_BOT_USER_SQL,
            user.id,
            user.username,
            user.first_name,
            user.last_name,
        )
