from pathlib import Path
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.config import settings
from aiogram import F
from aiogram.types import ReplyKeyboardRemove
from app.keyboards.cancel_keyboard import cancel_keyboard
from app.keyboards.speaker_keyboard import build_speaker_keyboard
from app.parsers.zoom_parser import TranscriptSegment
from app.services.extraction_service import extract_transcript
from app.services.file_service import delete_file, write_text_file
from app.services.summary_service import generate_summary
from app.utils.time_utils import canonical_time, is_valid_time_format
from app.keyboards.summary_keyboard import build_summary_keyboard

router = Router()
logger = logging.getLogger(__name__)


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


async def cleanup_state_files(state: FSMContext) -> None:
    data = await state.get_data()

    file_path = data.get("file_path")
    output_file_path = data.get("output_file_path")

    if file_path:
        delete_file(Path(file_path))
    if output_file_path:
        delete_file(Path(output_file_path))


@router.message(Command("cancel"))
async def cancel_flow(message: Message, state: FSMContext) -> None:
    await cleanup_state_files(state)
    await state.clear()
    await message.answer(
        "❌ Current flow cancelled.\n\n"
        "Send another .txt file whenever you're ready to process a new transcript.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text == "❌ Cancel")
async def cancel_via_button(message: Message, state: FSMContext):
    await cleanup_state_files(state)
    await state.clear()

    await message.answer(
        "❌ Current process cancelled.\n\n"
        "Send another .txt file whenever you're ready to process a new transcript.",
        reply_markup=ReplyKeyboardRemove()
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
        "⏱ Send START time (optional)\n"
        "Example: 12:30 or 13:30:45\n\n"
        "Type 'skip' to continue without a start time.",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(ExtractFlow.waiting_for_start_time)
async def receive_start_time(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if raw_value == "❌ Cancel":
        await cleanup_state_files(state)
        await state.clear()
        await message.answer(
            "❌ Current process cancelled.\n\n"
            "Send another .txt file whenever you're ready to process a new transcript.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if raw_value.lower() == "skip":
        await state.update_data(start_time=None)
    else:
        if not is_valid_time_format(raw_value):
            await message.answer(
                "Invalid START time format.\n"
                "Use HH:MM or HH:MM:SS, or send skip."
            )
            return
        await state.update_data(start_time=canonical_time(raw_value))

    await state.set_state(ExtractFlow.waiting_for_end_time)
    await message.answer(
    "⏱ Send END time (optional)\n"
    "Example: 12:30 or 13:30:45\n\n"
    "Type 'skip' to continue without an end time.",
    reply_markup=cancel_keyboard()
)


@router.message(ExtractFlow.waiting_for_end_time)
async def receive_end_time_and_process(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if raw_value == "❌ Cancel":
        await cleanup_state_files(state)
        await state.clear()
        await message.answer(
            "❌ Current process cancelled.\n\n"
            "Send another .txt file whenever you're ready to process a new transcript.",
            reply_markup=ReplyKeyboardRemove()
        )
        return


    if raw_value.lower() == "skip":
        end_time = None
    else:
        if not is_valid_time_format(raw_value):
            await message.answer(
                "Invalid END time format.\n"
                "Use HH:MM or HH:MM:SS, or send skip.",
                reply_markup=cancel_keyboard()
            )
            return
        end_time = canonical_time(raw_value)

    await state.update_data(end_time=end_time)
    data = await state.get_data()

    selected_speakers = data["selected_speakers"]
    start_time = data.get("start_time")
    segments = [TranscriptSegment.from_dict(item) for item in data["segments"]]

    await message.answer("Processing transcript...")

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
                "No matching transcript segments were found for those filters."
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
            "🎉 Extraction complete!\n\n"
            f"👤 Speaker(s): {', '.join(result.speakers)}\n"
            f"📊 Segments found: {result.segment_count}\n"
            f"⏱ Start filter: {start_time or 'not set'}\n"
            f"⏱ End filter: {end_time or 'not set'}",
            reply_markup=ReplyKeyboardRemove()
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
            "Would you like an AI summary for this transcript?",
            reply_markup=build_summary_keyboard(),
        )


    except Exception as exc:
        logger.exception("Extraction flow failed: %s", exc)
        await cleanup_state_files(state)
        await state.clear()
        await message.answer("Something went wrong during extraction.")


@router.callback_query(
    ExtractFlow.waiting_for_summary_decision,
    F.data == "summary_yes"
)
async def generate_summary_on_approval(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    transcript_text = data.get("final_transcript", "")

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🧠 Generating summary...")

    try:
        summary = await generate_summary(transcript_text, mode="short")

        if callback.message:
            for chunk in split_long_text(
                f"🧠 Summary\n\n{summary}",
                settings.max_message_chars,
            ):
                await callback.message.answer(chunk)

            await callback.message.answer(
                "✅ Summary is ready.\n\n"
                "Send another .txt file whenever you want to process a new transcript."
            )

    except Exception as exc:
        logger.exception("Summary generation failed: %s", exc)
        if callback.message:
            await callback.message.answer("⚠️ Failed to generate summary.")

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
            "👍 Okay, summary skipped.\n\n"
            "Send another .txt file whenever you want to process a new transcript."
        )

    await cleanup_state_files(state)
    await state.clear()
    await callback.answer()
