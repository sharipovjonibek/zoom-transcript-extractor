from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from app.services.broadcast_service import broadcast_update

router = Router()

ADMIN_ID = 6371353927  


@router.message(Command("broadcast"))
async def send_broadcast(message: Message, bot):
    if message.from_user.id != ADMIN_ID:
        return

    success, failed = await broadcast_update(bot)

    await message.answer(
        f"✅ Broadcast done\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )