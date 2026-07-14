import unittest

from app.parsers.zoom_parser import TranscriptSegment
from app.services.extraction_service import extract_transcript, next_known_start_time


class ExtractionServiceTests(unittest.TestCase):
    def test_filters_selected_speaker_case_insensitively(self) -> None:
        segments = [
            TranscriptSegment(speaker="Alice", text="Alpha", start_time="00:00"),
            TranscriptSegment(speaker="Bob", text="Beta", start_time="01:00"),
        ]

        result = extract_transcript(segments, selected_speakers=["alice"])

        self.assertEqual(result.segment_count, 1)
        self.assertEqual(result.segments[0].speaker, "Alice")

    def test_uses_next_start_time_as_effective_end_for_filtering(self) -> None:
        segments = [
            TranscriptSegment(speaker="Alice", text="Long opening", start_time="00:00"),
            TranscriptSegment(speaker="Bob", text="Response", start_time="05:00"),
        ]

        result = extract_transcript(
            segments,
            selected_speakers=["Alice"],
            start_time="03:00",
            end_time="04:00",
        )

        self.assertEqual(result.segment_count, 1)
        self.assertIn("Long opening", result.transcript)

    def test_next_known_start_time_returns_later_timestamp(self) -> None:
        segments = [
            TranscriptSegment(speaker="Alice", text="A", start_time="00:00"),
            TranscriptSegment(speaker="Bob", text="B", start_time=None),
            TranscriptSegment(speaker="Carol", text="C", start_time="02:00"),
        ]

        self.assertEqual(next_known_start_time(segments, 0), "02:00")


if __name__ == "__main__":
    unittest.main()
