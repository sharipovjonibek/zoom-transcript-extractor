import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.db import close_db, init_db
from app.handlers.extract_flow import router as extract_flow_router
from app.handlers.prompt_library import router as prompt_library_router
from app.handlers.start import router as start_router
from app.handlers.upload import router as upload_router
from app.services.file_service import cleanup_old_temp_files, ensure_storage_dirs
from app.services.user_service import init_user_table


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is missing. Add it to your .env file.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        ensure_storage_dirs()
        cleanup_old_temp_files()
    except Exception as exc:
        logging.warning("Temp storage cleanup failed during startup: %s", exc)

    await init_db()
    await init_user_table()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(prompt_library_router)
    dp.include_router(upload_router)
    dp.include_router(extract_flow_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())