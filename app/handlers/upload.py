import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.handlers.extract_flow import ExtractFlow
from app.keyboards.speaker_keyboard import build_speaker_keyboard
from app.parsers.zoom_parser import extract_speaker_names, parse_zoom_transcript
from app.services.file_service import delete_file, download_user_file, read_text_file
from app.keyboards.cancel_keyboard import cancel_keyboard
from pathlib import Path
from app.services.user_service import track_user_request



router = Router()
logger = logging.getLogger(__name__)


@router.message(F.document)
async def handle_transcript_upload(message: Message, state: FSMContext) -> None:

    if message.from_user:
        await track_user_request(message.from_user)


    current_state = await state.get_state()
    if current_state is not None:
        await cleanup_previous_flow(state)

    document = message.document

    if document is None:
        await message.answer("Please send a valid .txt file.")
        return

    file_name = (document.file_name or "").lower()
    if not file_name.endswith(".txt"):
        await message.answer("Please upload a valid Zoom transcript .txt file.")
        return

    saved_path = await download_user_file(message.bot, document)

    try:
        raw_text = read_text_file(saved_path)
        segments = parse_zoom_transcript(raw_text)
        speakers = extract_speaker_names(segments)

        if not segments or not speakers:
            delete_file(saved_path)
            await message.answer(
                "I could not detect speakers in this file. "
                "Please upload a valid Zoom transcript .txt file."
            )
            return

        await state.clear()
        await state.update_data(
            file_path=str(saved_path),
            segments=[segment.to_dict() for segment in segments],
            available_speakers=speakers,
            selected_speaker_indexes=[],
        )
        await state.set_state(ExtractFlow.waiting_for_speaker_selection)

        keyboard = build_speaker_keyboard(
            speakers=speakers,
            selected_indexes=[],
        )

        speaker_list_preview = "\n".join(f"👤 {speaker}" for speaker in speakers[:20])
        if len(speakers) > 20:
            speaker_list_preview += "\n- ..."

        await message.answer(
            "📂 Transcript received!\n\n"
            "I detected these speakers:\n"
            f"{speaker_list_preview}\n\n"
            "Select up to 2 speakers, then press ✅ Done.",
            reply_markup=keyboard,
        )
        await message.answer(
            "You can cancel anytime.",
            reply_markup=cancel_keyboard()
        )

    except Exception as exc:
        logger.exception("Failed to process uploaded transcript: %s", exc)
        delete_file(saved_path)
        await message.answer(
            "Something went wrong while reading the transcript. "
            "Please try another .txt file."
        )


async def cleanup_previous_flow(state: FSMContext) -> None:
    data = await state.get_data()

    file_path = data.get("file_path")
    output_file_path = data.get("output_file_path")

    if file_path:
        delete_file(Path(file_path))

    if output_file_path:
        delete_file(Path(output_file_path))

    await state.clear()
