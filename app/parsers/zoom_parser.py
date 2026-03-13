from __future__ import annotations

from dataclasses import asdict, dataclass
import re

TIME_PATTERN = r"\d{1,2}:\d{2}(?::\d{2})?"


@dataclass
class TranscriptSegment:
    speaker: str
    text: str
    start_time: str | None = None
    end_time: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptSegment":
        return cls(
            speaker=data.get("speaker", ""),
            text=data.get("text", ""),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
        )


RANGE_WITH_TEXT = re.compile(
    rf"^\[?(?P<start>{TIME_PATTERN})\]?\s*"
    rf"(?:-|–|—|->)\s*"
    rf"\[?(?P<end>{TIME_PATTERN})\]?\s+"
    rf"(?P<speaker>[^:]{1,120})"
    rf":\s*(?P<text>.*)$"
)

TIME_SPEAKER_TEXT = re.compile(
    rf"^\[?(?P<start>{TIME_PATTERN})\]?\s+"
    rf"(?P<speaker>[^:]{1,120})"
    rf":\s*(?P<text>.*)$"
)

SPEAKER_TIME_HEADER = re.compile(
    rf"^(?P<speaker>.+?)\s+(?P<start>{TIME_PATTERN})$"
)

TIME_SPEAKER_HEADER = re.compile(
    rf"^\[?(?P<start>{TIME_PATTERN})\]?\s+(?P<speaker>.+?)$"
)


def normalize_speaker_name(name: str) -> str:
    name = name.replace("\t", " ")
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip("-—–: ")
    return name


def parse_zoom_transcript(raw_text: str) -> list[TranscriptSegment]:
    text = raw_text.replace("\ufeff", "")
    lines = text.splitlines()

    segments: list[TranscriptSegment] = []
    current: TranscriptSegment | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        range_match = RANGE_WITH_TEXT.match(line)
        if range_match:
            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=normalize_speaker_name(range_match.group("speaker")),
                text=(range_match.group("text") or "").strip(),
                start_time=range_match.group("start"),
                end_time=range_match.group("end"),
            )
            continue

        inline_match = TIME_SPEAKER_TEXT.match(line)
        if inline_match:
            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=normalize_speaker_name(inline_match.group("speaker")),
                text=(inline_match.group("text") or "").strip(),
                start_time=inline_match.group("start"),
                end_time=None,
            )
            continue

        speaker_time_header_match = SPEAKER_TIME_HEADER.match(line)
        if speaker_time_header_match:
            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=normalize_speaker_name(speaker_time_header_match.group("speaker")),
                text="",
                start_time=speaker_time_header_match.group("start"),
                end_time=None,
            )
            continue

        time_speaker_header_match = TIME_SPEAKER_HEADER.match(line)
        if time_speaker_header_match:
            possible_speaker = normalize_speaker_name(time_speaker_header_match.group("speaker"))

            # Avoid false positives like plain text lines that begin with a time but contain no real speaker.
            if 1 <= len(possible_speaker.split()) <= 8:
                if current and current.text.strip():
                    segments.append(current)

                current = TranscriptSegment(
                    speaker=possible_speaker,
                    text="",
                    start_time=time_speaker_header_match.group("start"),
                    end_time=None,
                )
                continue

        if current is not None:
            current.text = f"{current.text} {line}".strip()

    if current and current.text.strip():
        segments.append(current)

    return merge_duplicate_adjacent_segments(segments)


def merge_duplicate_adjacent_segments(
    segments: list[TranscriptSegment],
) -> list[TranscriptSegment]:
    if not segments:
        return []

    merged: list[TranscriptSegment] = [segments[0]]

    for segment in segments[1:]:
        last = merged[-1]

        if (
            segment.speaker.casefold() == last.speaker.casefold()
            and segment.start_time == last.start_time
            and segment.end_time == last.end_time
        ):
            last.text = f"{last.text} {segment.text}".strip()
        else:
            merged.append(segment)

    return merged


def extract_speaker_names(segments: list[TranscriptSegment]) -> list[str]:
    seen: set[str] = set()
    speakers: list[str] = []

    for segment in segments:
        speaker = normalize_speaker_name(segment.speaker)
        key = speaker.casefold()

        if speaker and key not in seen:
            seen.add(key)
            speakers.append(speaker)

    return speakers