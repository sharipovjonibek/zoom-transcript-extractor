import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message, ReplyKeyboardRemove

from app.config import settings
from app.keyboards.cancel_keyboard import CANCEL_BUTTON, SKIP_BUTTON, cancel_keyboard, time_filter_keyboard
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.keyboards.speaker_keyboard import build_speaker_keyboard
from app.parsers.zoom_parser import TranscriptSegment
from app.services.extraction_service import extract_transcript
from app.services.file_service import write_text_file
from app.services.session_service import cleanup_state_files
from app.services.summary_service import generate_summary
from app.keyboards.summary_keyboard import build_summary_keyboard
from app.utils.time_utils import canonical_time, is_valid_time_format, is_valid_time_range

router = Router()
logger = logging.getLogger(__name__)

TEXT_SKIP = "skip"


class ExtractFlow(StatesGroup):
    waiting_for_speaker_selection = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()
    waiting_for_summary_decision = State()


def split_long_text(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    current = ""

    for block in text.split("\n\n"):
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(block) <= max_len:
            current = block
            continue

        for i in range(0, len(block), max_len):
            chunks.append(block[i:i + max_len])

    if current:
        chunks.append(current)

    return chunks


def is_cancel_text(value: str) -> bool:
    return value == CANCEL_BUTTON


def is_skip_text(value: str) -> bool:
    return value == SKIP_BUTTON or value.casefold() == TEXT_SKIP


@router.message(Command("cancel"))
async def cancel_flow(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()
    await message.answer(
        "❌ Current flow cancelled.\n\n"
        "Send another .txt file whenever you're ready to process a new transcript.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "❌ Cancel")
async def cancel_via_button(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()

    await message.answer(
        "❌ Current process cancelled.\n\n"
        "Send another .txt file whenever you're ready to process a new transcript.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(
    ExtractFlow.waiting_for_speaker_selection,
    F.data.startswith("speaker:")
)
async def toggle_speaker(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    speakers: list[str] = data.get("available_speakers", [])
    selected_indexes: list[int] = data.get("selected_speaker_indexes", [])

    try:
        index = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Invalid selection.", show_alert=True)
        return

    if index < 0 or index >= len(speakers):
        await callback.answer("Speaker not found.", show_alert=True)
        return

    selected_set = set(selected_indexes)

    if index in selected_set:
        selected_set.remove(index)
        selected_now = sorted(selected_set)
        await state.update_data(selected_speaker_indexes=selected_now)
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=build_speaker_keyboard(speakers, selected_now)
            )
        await callback.answer("➖ Speaker removed")
        return

    if len(selected_set) >= 2:
        await callback.answer("⚠️ You can select up to 2 speakers only.", show_alert=True)
        return

    selected_set.add(index)
    selected_now = sorted(selected_set)
    await state.update_data(selected_speaker_indexes=selected_now)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=build_speaker_keyboard(speakers, selected_now)
        )

    await callback.answer("✅ Speaker selected")


@router.callback_query(
    ExtractFlow.waiting_for_speaker_selection,
    F.data == "speaker_reset"
)
async def reset_speaker_selection(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    speakers: list[str] = data.get("available_speakers", [])
    selected_indexes: list[int] = data.get("selected_speaker_indexes", [])

    if not selected_indexes:
        await callback.answer("Nothing to reset.")
        return

    await state.update_data(selected_speaker_indexes=[])

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=build_speaker_keyboard(speakers, [])
        )

    await callback.answer("🔄 Selection reset")


@router.callback_query(
    ExtractFlow.waiting_for_speaker_selection,
    F.data == "speaker_done"
)
async def finish_speaker_selection(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    speakers: list[str] = data.get("available_speakers", [])
    selected_indexes: list[int] = data.get("selected_speaker_indexes", [])

    if not selected_indexes:
        await callback.answer("⚠️ Select at least 1 speaker first.", show_alert=True)
        return

    selected_speakers = [speakers[i] for i in selected_indexes]
    await state.update_data(selected_speakers=selected_speakers)
    await state.set_state(ExtractFlow.waiting_for_start_time)

    if callback.message:
        await callback.message.answer(
            "✅ Speakers selected\n\n"
            f"👥 Selected: {', '.join(selected_speakers)}\n\n"
            "Step 2 of 3: optional time filter\n\n"
            "Send the START time, or tap ⏭ Skip to start from the beginning.\n\n"
            "Examples: 12:30, 01:13:45",
            reply_markup=time_filter_keyboard(),
        )
    await callback.answer()


@router.message(ExtractFlow.waiting_for_speaker_selection)
async def remind_speaker_selection(message: Message) -> None:
    await message.answer(
        "Please select speaker(s) using the buttons above, then tap ✅ Continue.",
        reply_markup=cancel_keyboard(),
    )


@router.message(ExtractFlow.waiting_for_start_time)
async def receive_start_time(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if is_cancel_text(raw_value):
        await cleanup_state_files(state)
        await state.clear()
        await message.answer(
            "❌ Current process cancelled.\n\n"
            "Send another .txt file whenever you're ready to process a new transcript.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if is_skip_text(raw_value):
        await state.update_data(start_time=None)
    else:
        if not is_valid_time_format(raw_value):
            await message.answer(
                "⚠️ Invalid START time.\n\n"
                "Use HH:MM or HH:MM:SS, for example 12:30 or 01:13:45.\n"
                "You can also tap ⏭ Skip.",
                reply_markup=time_filter_keyboard(),
            )
            return
        await state.update_data(start_time=canonical_time(raw_value))

    await state.set_state(ExtractFlow.waiting_for_end_time)
    await message.answer(
        "Now send the END time, or tap ⏭ Skip to continue to the end of the transcript.\n\n"
        "Examples: 12:45, 01:25:00",
        reply_markup=time_filter_keyboard(),
    )


@router.message(ExtractFlow.waiting_for_end_time)
async def receive_end_time_and_process(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if is_cancel_text(raw_value):
        await cleanup_state_files(state)
        await state.clear()
        await message.answer(
            "❌ Current process cancelled.\n\n"
            "Send another .txt file whenever you're ready to process a new transcript.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if is_skip_text(raw_value):
        end_time = None
    else:
        if not is_valid_time_format(raw_value):
            await message.answer(
                "⚠️ Invalid END time.\n\n"
                "Use HH:MM or HH:MM:SS, for example 12:45 or 01:25:00.\n"
                "You can also tap ⏭ Skip.",
                reply_markup=time_filter_keyboard(),
            )
            return
        end_time = canonical_time(raw_value)

    data = await state.get_data()
    start_time = data.get("start_time")
    if not is_valid_time_range(start_time, end_time):
        await message.answer(
            "⚠️ Invalid time range.\n\n"
            "END time must be the same as or later than START time.",
            reply_markup=time_filter_keyboard(),
        )
        return

    await state.update_data(end_time=end_time)
    data = await state.get_data()

    selected_speakers = data["selected_speakers"]
    segments = [TranscriptSegment.from_dict(item) for item in data["segments"]]

    await message.answer("⏳ Processing transcript...")

    try:
        result = extract_transcript(
            segments=segments,
            selected_speakers=selected_speakers,
            start_time=start_time,
            end_time=end_time,
        )

        if not result.segments:
            await cleanup_state_files(state)
            await state.clear()
            await message.answer(
                "No matching transcript segments were found for those filters.\n\n"
                "Try a wider time range or select a different speaker.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        output_path = write_text_file(
            content=result.transcript,
            prefix="clean_transcript_",
            suffix=".txt",
        )

        await state.update_data(
            output_file_path=str(output_path),
            final_transcript=result.transcript,
            final_speakers=result.speakers,
            final_segment_count=result.segment_count,
            final_start_time=start_time,
            final_end_time=end_time,
        )

        await message.answer(
            "✅ Extraction complete\n\n"
            f"👤 Speaker(s): {', '.join(result.speakers)}\n"
            f"📊 Segments found: {result.segment_count}\n"
            f"⏱ Start filter: {start_time or 'not set'}\n"
            f"⏱ End filter: {end_time or 'not set'}",
            reply_markup=ReplyKeyboardRemove(),
        )

        await message.answer_document(
            BufferedInputFile(
                file=output_path.read_bytes(),
                filename=output_path.name,
            ),
            caption="📄 Here is your cleaned transcript file.",
        )

        await state.set_state(ExtractFlow.waiting_for_summary_decision)

        await message.answer(
            "Step 3 of 3: would you like an AI summary for this cleaned transcript?",
            reply_markup=build_summary_keyboard(),
        )

    except Exception as exc:
        logger.exception("Extraction flow failed: %s", exc)
        await cleanup_state_files(state)
        await state.clear()
        await message.answer(
            "⚠️ Something went wrong during extraction.\n\n"
            "Please try again with another transcript file.",
            reply_markup=get_main_menu_keyboard(),
        )


@router.callback_query(
    ExtractFlow.waiting_for_summary_decision,
    F.data == "summary_yes"
)
async def generate_summary_on_approval(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    transcript_text = data.get("final_transcript", "")

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🧠 Generating summary. This may take a moment...")

    try:
        summary = await generate_summary(transcript_text, mode="short")

        if callback.message:
            for chunk in split_long_text(
                f"🧠 Summary\n\n{summary}",
                settings.max_message_chars,
            ):
                await callback.message.answer(chunk)

            await callback.message.answer(
                "✅ Done. You can upload another transcript whenever you are ready.",
                reply_markup=get_main_menu_keyboard(),
            )

    except Exception as exc:
        logger.exception("Summary generation failed: %s", exc)
        if callback.message:
            await callback.message.answer(
                "⚠️ Failed to generate summary.\n\n"
                "The cleaned transcript file was already sent above.",
                reply_markup=get_main_menu_keyboard(),
            )

    finally:
        await cleanup_state_files(state)
        await state.clear()
        await callback.answer()


@router.callback_query(
    ExtractFlow.waiting_for_summary_decision,
    F.data == "summary_skip"
)
async def skip_summary(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "✅ Done. Summary skipped.\n\n"
            "You can upload another transcript whenever you are ready.",
            reply_markup=get_main_menu_keyboard(),
        )

    await cleanup_state_files(state)
    await state.clear()
    await callback.answer()


@router.message(ExtractFlow.waiting_for_summary_decision)
async def remind_summary_decision(message: Message) -> None:
    await message.answer(
        "Please choose one of the summary options above.",
        reply_markup=ReplyKeyboardRemove(),
    )
