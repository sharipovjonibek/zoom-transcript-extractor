from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Transcript Extraction")],
            [KeyboardButton(text="🧠 Prompt Library")],
        ],
        resize_keyboard=True,
    )