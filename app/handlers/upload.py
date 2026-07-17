import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.handlers.extract_flow import ExtractFlow
from app.keyboards.cancel_keyboard import cancel_keyboard
from app.keyboards.speaker_keyboard import build_speaker_keyboard
from app.parsers.zoom_parser import extract_speaker_names, parse_zoom_transcript
from app.services.file_service import delete_file, download_user_file, read_text_file
from app.services.session_service import cleanup_state_files
from app.services.user_service import track_user_request

router = Router()
logger = logging.getLogger(__name__)

SUPPORTED_TRANSCRIPT_SUFFIXES = (".txt", ".vtt")
SUPPORTED_FORMATS_TEXT = "`.txt` or `.vtt`"


def is_supported_transcript_file(file_name: str) -> bool:
    return file_name.lower().endswith(SUPPORTED_TRANSCRIPT_SUFFIXES)


@router.message(F.document)
async def handle_transcript_upload(message: Message, state: FSMContext) -> None:
    if message.from_user:
        await track_user_request(message.from_user)

    current_state = await state.get_state()
    if current_state is not None:
        await cleanup_state_files(state)
        await state.clear()

    document = message.document

    if document is None:
        await message.answer(
            f"Please upload a Zoom transcript file in {SUPPORTED_FORMATS_TEXT} format.",
            parse_mode="Markdown",
        )
        return

    file_name = (document.file_name or "").lower()
    if not is_supported_transcript_file(file_name):
        await message.answer(
            f"⚠️ I can only process Zoom transcript files in {SUPPORTED_FORMATS_TEXT} format.\n\n"
            "Please export or download the transcript in one of those formats and upload it here.",
            parse_mode="Markdown",
        )
        return

    if document.file_size and document.file_size > settings.max_upload_bytes:
        limit_mb = settings.max_upload_bytes / (1024 * 1024)
        await message.answer(
            "⚠️ This transcript is too large to process safely.\n\n"
            f"Current upload limit: {limit_mb:.1f} MB."
        )
        return

    await message.answer("📥 File received. Reading transcript and detecting speakers...")

    saved_path = await download_user_file(message.bot, document)

    try:
        raw_text = read_text_file(saved_path)
        segments = parse_zoom_transcript(raw_text)
        speakers = extract_speaker_names(segments)

        if not segments or not speakers:
            delete_file(saved_path)
            await message.answer(
                "⚠️ I could not detect speakers in this file.\n\n"
                f"Please upload a Zoom transcript {SUPPORTED_FORMATS_TEXT} file "
                "that includes speaker names and timestamps.",
                parse_mode="Markdown",
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
            "✅ Transcript ready\n\n"
            f"Detected speakers: {len(speakers)}\n\n"
            f"{speaker_list_preview}\n\n"
            "Step 1 of 3: select 1 or 2 speakers, then tap ✅ Continue.",
            reply_markup=keyboard,
        )
        await message.answer(
            "Use ❌ Cancel anytime to stop this process.",
            reply_markup=cancel_keyboard(),
        )

    except Exception as exc:
        logger.exception("Failed to process uploaded transcript: %s", exc)
        delete_file(saved_path)
        await message.answer(
            "⚠️ Something went wrong while reading the transcript.\n\n"
            f"Please try another Zoom {SUPPORTED_FORMATS_TEXT} transcript file.",
            parse_mode="Markdown",
        )
