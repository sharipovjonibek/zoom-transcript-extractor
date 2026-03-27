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


GET_ALL_BOT_USER_IDS_SQL = """
SELECT telegram_user_id
FROM bot_users
ORDER BY first_seen_at;
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


async def get_all_user_ids() -> list[int]:
    pool = get_db_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(GET_ALL_BOT_USER_IDS_SQL)

    return [row["telegram_user_id"] for row in rows]