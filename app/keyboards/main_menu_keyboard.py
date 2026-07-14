from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

NEW_TRANSCRIPT_BUTTON = "📄 New Transcript"
HELP_BUTTON = "ℹ️ Help"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=NEW_TRANSCRIPT_BUTTON)],
            [KeyboardButton(text=HELP_BUTTON)],
        ],
        resize_keyboard=True,
    )
