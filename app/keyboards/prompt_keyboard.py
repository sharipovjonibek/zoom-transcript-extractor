from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.data.prompts import PROMPT_LIBRARY


def get_prompt_categories_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    for category_key, category_data in PROMPT_LIBRARY.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=category_data["title"],
                    callback_data=f"prompt_category:{category_key}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="prompt_back_main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_prompts_keyboard(category_key: str) -> InlineKeyboardMarkup:
    keyboard = []

    prompts = PROMPT_LIBRARY[category_key]["prompts"]

    for prompt in prompts:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=prompt["title"],
                    callback_data=f"prompt_select:{category_key}:{prompt['id']}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="🔙 Back to Categories", callback_data="prompt_back_categories")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_prompt_result_keyboard(category_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back to Prompts",
                    callback_data=f"prompt_category:{category_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Back to Main Menu",
                    callback_data="prompt_back_main",
                )
            ],
        ]
    )