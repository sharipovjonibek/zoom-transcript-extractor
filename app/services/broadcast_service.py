import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.services.user_service import get_all_user_ids

logger = logging.getLogger(__name__)


async def broadcast_update(bot: Bot):
    users = await get_all_user_ids()

    text = (
        "📄 Zoom Transcript Extractor Bot\n\n"
        "Upload a Zoom transcript .txt or .vtt file and I can extract selected speakers, "
        "apply optional time filters, generate a clean transcript, and create an AI summary.\n\n"
        "Start by pressing 👉 /start"
    )

    success = 0
    failed = 0

    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                text,
                reply_markup=get_main_menu_keyboard(),
            )
            success += 1
            await asyncio.sleep(0.05)  # avoid rate limit
        except TelegramForbiddenError:
            failed += 1  # user blocked bot
        except Exception as exc:
            logger.warning("Failed to broadcast to user %s: %s", user_id, exc)
            failed += 1

    return success, failed
