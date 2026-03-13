from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_speaker_keyboard(
    speakers: list[str],
    selected_indexes: list[int],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    selected_set = set(selected_indexes)

    for index, speaker in enumerate(speakers):
        label = f"✅ {speaker}" if index in selected_set else f"👤 {speaker}"
        builder.button(text=label, callback_data=f"speaker:{index}")

    builder.button(text="✅ Done", callback_data="speaker_done")
    builder.button(text="🔄 Reset", callback_data="speaker_reset")

    layout = [1] * len(speakers) + [2]
    builder.adjust(*layout)

    return builder.as_markup()