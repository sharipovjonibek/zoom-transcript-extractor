import re

from app.parsers.zoom_parser import TranscriptSegment


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text.strip()


def clean_segment_text(text: str) -> str:
    text = normalize_whitespace(text)
    text = text.strip("-—– ")
    return text


def render_clean_transcript(segments: list[TranscriptSegment]) -> str:
    blocks: list[str] = []

    for segment in segments:
        body = clean_segment_text(segment.text)
        if not body:
            continue

        if segment.start_time and segment.end_time:
            header = f"[{segment.start_time} - {segment.end_time}] {segment.speaker}:"
        elif segment.start_time:
            header = f"[{segment.start_time}] {segment.speaker}:"
        else:
            header = f"{segment.speaker}:"

        blocks.append(f"{header}\n{body}")

    return "\n\n".join(blocks)