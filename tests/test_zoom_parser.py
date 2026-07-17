import unittest

from app.parsers.zoom_parser import extract_speaker_names, parse_zoom_transcript


class ZoomParserTests(unittest.TestCase):
    def test_sentence_ending_with_time_is_not_speaker_header(self) -> None:
        raw_text = "\n".join(
            [
                "John Doe 00:00",
                "We should meet at 12:30",
                "Continue with next action",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "John Doe")
        self.assertIn("We should meet at 12:30", segments[0].text)
        self.assertIn("Continue with next action", segments[0].text)

    def test_parses_common_header_and_inline_formats(self) -> None:
        raw_text = "\n".join(
            [
                "[00:00 - 00:10] Alice: Welcome everyone",
                "00:12 Bob: Thanks",
                "00:20 Carol",
                "I have an update",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual([segment.speaker for segment in segments], ["Alice", "Bob", "Carol"])
        self.assertEqual(segments[0].end_time, "00:10")
        self.assertEqual(segments[2].text, "I have an update")

    def test_extracts_unique_speakers_case_insensitively(self) -> None:
        raw_text = "\n".join(
            [
                "00:00 Alice: First",
                "00:01 alice: Second",
                "00:02 Bob: Third",
            ]
        )

        speakers = extract_speaker_names(parse_zoom_transcript(raw_text))

        self.assertEqual(speakers, ["Alice", "Bob"])

    def test_allows_common_zoom_name_punctuation(self) -> None:
        raw_text = "\n".join(
            [
                "00:00 Dr. Jane: First",
                "00:01 john.doe@example.com: Second",
            ]
        )

        speakers = extract_speaker_names(parse_zoom_transcript(raw_text))

        self.assertEqual(speakers, ["Dr. Jane", "john.doe@example.com"])


if __name__ == "__main__":
    unittest.main()
