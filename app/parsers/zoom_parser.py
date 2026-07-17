from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import re

TIME_PATTERN = r"\d{1,2}:\d{2}(?::\d{2})?"
VTT_TIMESTAMP_PATTERN = r"(?:\d{1,3}:)?\d{2}:\d{2}(?:\.\d{1,3})?"


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
    rf"(?P<speaker>[^:]{{1,120}})"
    rf":\s*(?P<text>.*)$"
)

TIME_SPEAKER_TEXT = re.compile(
    rf"^\[?(?P<start>{TIME_PATTERN})\]?\s+"
    rf"(?P<speaker>[^:]{{1,120}})"
    rf":\s*(?P<text>.*)$"
)

SPEAKER_TIME_HEADER = re.compile(
    rf"^(?P<speaker>.+?)\s+(?P<start>{TIME_PATTERN})$"
)

TIME_SPEAKER_HEADER = re.compile(
    rf"^\[?(?P<start>{TIME_PATTERN})\]?\s+(?P<speaker>.+?)$"
)

VTT_CUE_TIMING = re.compile(
    rf"^(?P<start>{VTT_TIMESTAMP_PATTERN})\s+-->\s+"
    rf"(?P<end>{VTT_TIMESTAMP_PATTERN})(?:\s+.*)?$"
)

VTT_VOICE_TAG = re.compile(r"<v\s+(?P<speaker>[^>]+)>(?P<text>.*)", re.IGNORECASE)

SPEAKER_TEXT = re.compile(
    r"^(?P<speaker>[^:]{1,120}):\s*(?P<text>.*)$"
)


def normalize_speaker_name(name: str) -> str:
    name = name.replace("\t", " ")
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip("-—–: ")
    return name


def looks_like_speaker_name(name: str) -> bool:
    name = normalize_speaker_name(name)
    if not name:
        return False

    if any(mark in name for mark in "?!;") or name.endswith("."):
        return False

    words = re.findall(r"[A-Za-z0-9_@.'()-]+", name)
    if not 1 <= len(words) <= 6:
        return False

    if words[0].casefold() in {"i", "we", "you", "they", "he", "she", "it"}:
        return False

    if len(words) <= 2:
        return True

    lowercase_words = sum(word.isalpha() and word.islower() for word in words)
    if lowercase_words >= 2:
        return False

    title_like_words = sum(
        bool(word[:1].isupper())
        or word.isupper()
        or any(char.isdigit() for char in word)
        or any(char in word for char in "@_.()-")
        for word in words
    )
    return title_like_words >= len(words) - 1


def parse_zoom_transcript(raw_text: str) -> list[TranscriptSegment]:
    text = raw_text.replace("\ufeff", "")

    if looks_like_webvtt(text):
        return parse_webvtt_transcript(text)

    lines = text.splitlines()

    segments: list[TranscriptSegment] = []
    current: TranscriptSegment | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        range_match = RANGE_WITH_TEXT.match(line)
        if range_match:
            speaker = normalize_speaker_name(range_match.group("speaker"))
            if not looks_like_speaker_name(speaker):
                if current is not None:
                    current.text = f"{current.text} {line}".strip()
                continue

            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=speaker,
                text=(range_match.group("text") or "").strip(),
                start_time=range_match.group("start"),
                end_time=range_match.group("end"),
            )
            continue

        inline_match = TIME_SPEAKER_TEXT.match(line)
        if inline_match:
            speaker = normalize_speaker_name(inline_match.group("speaker"))
            if not looks_like_speaker_name(speaker):
                if current is not None:
                    current.text = f"{current.text} {line}".strip()
                continue

            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=speaker,
                text=(inline_match.group("text") or "").strip(),
                start_time=inline_match.group("start"),
                end_time=None,
            )
            continue

        speaker_time_header_match = SPEAKER_TIME_HEADER.match(line)
        if speaker_time_header_match:
            speaker = normalize_speaker_name(speaker_time_header_match.group("speaker"))
            if not looks_like_speaker_name(speaker):
                if current is not None:
                    current.text = f"{current.text} {line}".strip()
                continue

            if current and current.text.strip():
                segments.append(current)

            current = TranscriptSegment(
                speaker=speaker,
                text="",
                start_time=speaker_time_header_match.group("start"),
                end_time=None,
            )
            continue

        time_speaker_header_match = TIME_SPEAKER_HEADER.match(line)
        if time_speaker_header_match:
            possible_speaker = normalize_speaker_name(time_speaker_header_match.group("speaker"))

            # Avoid false positives like plain text lines that begin with a time but contain no real speaker.
            if looks_like_speaker_name(possible_speaker):
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


def looks_like_webvtt(raw_text: str) -> bool:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return False

    if lines[0].startswith("WEBVTT"):
        return True

    return any(VTT_CUE_TIMING.match(line) for line in lines[:20])


def parse_webvtt_transcript(raw_text: str) -> list[TranscriptSegment]:
    text = raw_text.replace("\ufeff", "")
    blocks = split_vtt_blocks(text)
    segments: list[TranscriptSegment] = []

    for block in blocks:
        if not block:
            continue

        cue_index = next(
            (index for index, line in enumerate(block) if VTT_CUE_TIMING.match(line.strip())),
            None,
        )
        if cue_index is None:
            continue

        first_line = block[0].strip()
        if first_line.startswith("NOTE") or first_line in {"STYLE", "REGION"}:
            continue

        timing_match = VTT_CUE_TIMING.match(block[cue_index].strip())
        if timing_match is None:
            continue

        speaker, cue_text = extract_webvtt_speaker_and_text(block[cue_index + 1:])
        if not cue_text:
            continue

        segments.append(
            TranscriptSegment(
                speaker=speaker,
                text=cue_text,
                start_time=normalize_webvtt_timestamp(timing_match.group("start")),
                end_time=normalize_webvtt_timestamp(timing_match.group("end")),
            )
        )

    return merge_duplicate_adjacent_segments(segments)


def split_vtt_blocks(raw_text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue

        current.append(line)

    if current:
        blocks.append(current)

    return blocks


def extract_webvtt_speaker_and_text(lines: list[str]) -> tuple[str, str]:
    speaker: str | None = None
    cleaned_lines: list[str] = []

    for line in lines:
        voice_match = VTT_VOICE_TAG.search(line)
        if voice_match:
            possible_speaker = normalize_speaker_name(voice_match.group("speaker"))
            if speaker is None and looks_like_speaker_name(possible_speaker):
                speaker = possible_speaker
            line = voice_match.group("text")

        cleaned_line = clean_webvtt_text(line)
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    text = " ".join(cleaned_lines).strip()
    if not text:
        return "Unknown Speaker", ""

    if speaker is None:
        speaker_match = SPEAKER_TEXT.match(text)
        if speaker_match:
            possible_speaker = normalize_speaker_name(speaker_match.group("speaker"))
            if looks_like_speaker_name(possible_speaker):
                speaker = possible_speaker
                text = speaker_match.group("text").strip()

    return speaker or "Unknown Speaker", text


def clean_webvtt_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_webvtt_timestamp(value: str) -> str:
    base_value = value.split(".", 1)[0]
    parts = [int(part) for part in base_value.split(":")]

    if len(parts) == 2:
        minutes, seconds = parts
        return f"00:{minutes:02d}:{seconds:02d}"

    hours, minutes, seconds = parts
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
