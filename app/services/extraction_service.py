from dataclasses import dataclass

from app.parsers.zoom_parser import TranscriptSegment
from app.utils.text_cleaner import clean_segment_text, render_clean_transcript
from app.utils.time_utils import segment_overlaps_requested_range


@dataclass
class ExtractionResult:
    speakers: list[str]
    start_time: str | None
    end_time: str | None
    segment_count: int
    segments: list[TranscriptSegment]
    transcript: str


def extract_transcript(
    segments: list[TranscriptSegment],
    selected_speakers: list[str],
    start_time: str | None = None,
    end_time: str | None = None,
) -> ExtractionResult:
    allowed = {speaker.casefold() for speaker in selected_speakers}
    filtered_segments: list[TranscriptSegment] = []

    for segment in segments:
        if segment.speaker.casefold() not in allowed:
            continue

        if not segment_overlaps_requested_range(
            segment_start=segment.start_time,
            segment_end=segment.end_time,
            requested_start=start_time,
            requested_end=end_time,
        ):
            continue

        cleaned_text = clean_segment_text(segment.text)
        if not cleaned_text:
            continue

        filtered_segments.append(
            TranscriptSegment(
                speaker=segment.speaker,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=cleaned_text,
            )
        )

    transcript = render_clean_transcript(filtered_segments)

    return ExtractionResult(
        speakers=selected_speakers,
        start_time=start_time,
        end_time=end_time,
        segment_count=len(filtered_segments),
        segments=filtered_segments,
        transcript=transcript,
    )