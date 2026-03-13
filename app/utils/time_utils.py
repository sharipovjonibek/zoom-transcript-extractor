import re

TIME_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


def is_valid_time_format(value: str) -> bool:
    value = value.strip()
    if not TIME_RE.match(value):
        return False

    parts = [int(part) for part in value.split(":")]

    if len(parts) == 2:
        hours, minutes = parts
        seconds = 0
    else:
        hours, minutes, seconds = parts

    return hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60


def canonical_time(value: str) -> str:
    parts = [int(part) for part in value.strip().split(":")]

    if len(parts) == 2:
        hours, minutes = parts
        return f"{hours:02d}:{minutes:02d}"

    hours, minutes, seconds = parts
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def time_to_seconds(value: str | None) -> int | None:
    if not value:
        return None

    value = canonical_time(value)
    parts = value.split(":")

    if len(parts) == 2:
        hours, minutes = map(int, parts)
        seconds = 0
    else:
        hours, minutes, seconds = map(int, parts)

    return hours * 3600 + minutes * 60 + seconds


def segment_overlaps_requested_range(
    segment_start: str | None,
    segment_end: str | None,
    requested_start: str | None,
    requested_end: str | None,
) -> bool:
    seg_start_seconds = time_to_seconds(segment_start)
    seg_end_seconds = time_to_seconds(segment_end)

    if seg_start_seconds is None:
        return True

    if seg_end_seconds is None:
        seg_end_seconds = seg_start_seconds

    req_start_seconds = time_to_seconds(requested_start)
    req_end_seconds = time_to_seconds(requested_end)

    if req_start_seconds is not None and seg_end_seconds < req_start_seconds:
        return False

    if req_end_seconds is not None and seg_start_seconds > req_end_seconds:
        return False

    return True