from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.data.prompts import PROMPT_LIBRARY
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.keyboards.prompt_keyboard import (
    get_prompt_categories_keyboard,
    get_prompt_result_keyboard,
    get_prompts_keyboard,
)

router = Router()


@router.message(F.text == "🧠 Prompt Library")
async def open_prompt_library(message: Message) -> None:
    await message.answer(
        "🧠 Prompt Library\n\nChoose a prompt category:",
        reply_markup=get_prompt_categories_keyboard(),
    )


@router.callback_query(F.data == "prompt_back_main")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏠 Back to main menu.\n\nChoose what you want to do next."
    )
    await callback.message.answer(
        "Main menu:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "prompt_back_categories")
async def back_to_categories(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🧠 Prompt Library\n\nChoose a prompt category:",
        reply_markup=get_prompt_categories_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prompt_category:"))
async def show_prompts_in_category(callback: CallbackQuery) -> None:
    category_key = callback.data.split(":")[1]

    if category_key not in PROMPT_LIBRARY:
        await callback.answer("Category not found.", show_alert=True)
        return

    category_title = PROMPT_LIBRARY[category_key]["title"]

    await callback.message.edit_text(
        f"{category_title}\n\nChoose a prompt:",
        reply_markup=get_prompts_keyboard(category_key),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prompt_select:"))
async def send_selected_prompt(callback: CallbackQuery) -> None:
    _, category_key, prompt_id = callback.data.split(":")

    if category_key not in PROMPT_LIBRARY:
        await callback.answer("Category not found.", show_alert=True)
        return

    prompts = PROMPT_LIBRARY[category_key]["prompts"]
    selected_prompt = next((prompt for prompt in prompts if prompt["id"] == prompt_id), None)

    if not selected_prompt:
        await callback.answer("Prompt not found.", show_alert=True)
        return

    text = (
        f"📌 <b>{selected_prompt['title']}</b>\n\n"
        f"<pre>{selected_prompt['text']}</pre>\n\n"
        "You can copy and use this prompt."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_prompt_result_keyboard(category_key),
        parse_mode="HTML",
    )
    await callback.answer()