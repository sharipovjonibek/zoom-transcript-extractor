from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.services.user_service import track_user_request

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    await state.clear()

    if message.from_user:
        await track_user_request(message.from_user)

    text = (
        "🚀 Zoom Transcript Extractor Bot\n\n"
        "Upload a Zoom transcript (.txt) and I will:\n\n"
        "👤 Extract messages from selected speaker(s)\n"
        "⏱ Apply optional time filtering\n"
        "📄 Generate a clean transcript\n"
        "🧠 Create an AI-powered summary\n\n"
        "📎 Send your transcript file to begin.\n\n"
        "💡 Tip: Use /cancel anytime to stop the current process."
    )

    await message.answer(text)