import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.services.user_service import get_all_user_ids


async def broadcast_update(bot: Bot):
    users = await get_all_user_ids()

    text = (
        "🔥 New Feature: Prompt Library\n\n"
        "I was going through our team Telegram groups and noticed that we often use prompts during work.\n"
        "But when you need them, scrolling through chat history is not very convenient.\n\n"
        "To solve this, I added a Prompt Library.\n"
        "Now you can quickly find and use the prompts you need.\n\n"
        "If you have useful prompts or any suggestions,\n"
        "feel free to reach out to @calculus_hero 🙌\n\n"
        "Try it now by pressing 👉 /start"
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
        except Exception:
            failed += 1

    return success, failed