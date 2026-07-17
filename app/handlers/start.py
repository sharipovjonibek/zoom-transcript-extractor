from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu_keyboard import (
    HELP_BUTTON,
    NEW_TRANSCRIPT_BUTTON,
    get_main_menu_keyboard,
)
from app.services.session_service import cleanup_state_files
from app.services.user_service import track_user_request

router = Router()

WELCOME_TEXT = (
    "🚀 Zoom Transcript Extractor\n\n"
    "Send a Zoom transcript `.txt` file and I will help you turn it into a clean, focused transcript.\n\n"
    "What I can do:\n"
    "👤 Extract one or two selected speakers\n"
    "⏱ Filter by meeting time\n"
    "📄 Return a cleaned transcript file\n"
    "🧠 Generate an optional meeting summary\n\n"
    "Tap 📄 New Transcript to begin."
)

HELP_TEXT = (
    "ℹ️ How to use the bot\n\n"
    "1. Tap 📄 New Transcript.\n"
    "2. Upload a Zoom `.txt` transcript file.\n"
    "3. Select up to 2 speakers.\n"
    "4. Add a start/end time or tap ⏭ Skip.\n"
    "5. Download the cleaned transcript.\n"
    "6. Choose whether to generate a summary.\n\n"
    "Accepted time examples: `12:30`, `01:12:45`.\n"
    "Use /cancel anytime to stop the current process."
)


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()

    if message.from_user:
        await track_user_request(message.from_user)

    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@router.message(Command("help"))
@router.message(F.text == HELP_BUTTON)
async def help_command(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@router.message(F.text == NEW_TRANSCRIPT_BUTTON)
@router.message(F.text == "📄 Transcript Extraction")
async def transcript_extraction_entry(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()
    await message.answer(
        "📄 New transcript\n\n"
        "Please upload your Zoom transcript as a `.txt` file.\n\n"
        "I will detect the speakers automatically and guide you through the next steps.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )


@router.message(StateFilter(None), Command("cancel"))
async def cancel_without_active_flow(message: Message) -> None:
    await message.answer(
        "There is no active process to cancel.\n\n"
        "Tap 📄 New Transcript when you are ready to upload a transcript.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(StateFilter(None), F.text)
async def handle_idle_text(message: Message) -> None:
    await message.answer(
        "Please tap 📄 New Transcript and upload a Zoom `.txt` transcript file.\n\n"
        "For guidance, tap ℹ️ Help.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )
