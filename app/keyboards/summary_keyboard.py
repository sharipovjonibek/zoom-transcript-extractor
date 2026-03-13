from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_summary_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Get Summary", callback_data="summary_yes")
    builder.button(text="⏭ Skip Summary", callback_data="summary_skip")
    builder.adjust(1)
    return builder.as_markup()
