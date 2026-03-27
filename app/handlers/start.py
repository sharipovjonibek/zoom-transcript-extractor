from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
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
        "You can also use the Prompt Library for ready-to-use prompts.\n\n"
        "💡 Tip: Use /cancel anytime to stop the current process."
    )

    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "📄 Transcript Extraction")
async def transcript_extraction_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📄 Transcript Extraction\n\n"
        "Please send your Zoom transcript file (.txt) to begin.\n\n"
        "You can also return and use Prompt Library anytime.",
        reply_markup=get_main_menu_keyboard(),
    )