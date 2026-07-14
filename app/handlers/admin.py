from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from app.config import settings
from app.services.broadcast_service import broadcast_update

router = Router()


@router.message(Command("broadcast"))
async def send_broadcast(message: Message, bot):
    if message.from_user is None or message.from_user.id != settings.admin_id:
        return

    success, failed = await broadcast_update(bot)

    await message.answer(
        f"✅ Broadcast done\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )
