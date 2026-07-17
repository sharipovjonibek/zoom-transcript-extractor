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

    def test_parses_webvtt_speaker_prefix_cues(self) -> None:
        raw_text = "\n".join(
            [
                "WEBVTT",
                "",
                "1",
                "00:00:01.000 --> 00:00:03.500 align:start position:0%",
                "Alice: Welcome everyone",
                "",
                "2",
                "00:00:04.000 --> 00:00:06.000",
                "Bob: Thanks Alice",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual([segment.speaker for segment in segments], ["Alice", "Bob"])
        self.assertEqual(segments[0].start_time, "00:00:01")
        self.assertEqual(segments[0].end_time, "00:00:03")
        self.assertEqual(segments[1].text, "Thanks Alice")

    def test_parses_webvtt_voice_tags_and_markup(self) -> None:
        raw_text = "\n".join(
            [
                "WEBVTT",
                "",
                "00:01.000 --> 00:03.000",
                "<v Dr. Jane><c.highlight>Hello &amp; welcome</c>",
                "to the sync",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "Dr. Jane")
        self.assertEqual(segments[0].start_time, "00:00:01")
        self.assertEqual(segments[0].text, "Hello & welcome to the sync")

    def test_webvtt_without_speaker_uses_unknown_speaker(self) -> None:
        raw_text = "\n".join(
            [
                "WEBVTT",
                "",
                "00:00:01.000 --> 00:00:02.000",
                "No speaker label here",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "Unknown Speaker")
        self.assertEqual(segments[0].text, "No speaker label here")

    def test_webvtt_without_blank_line_after_header_still_parses(self) -> None:
        raw_text = "\n".join(
            [
                "WEBVTT",
                "00:00:01.000 --> 00:00:02.000",
                "Alice: No blank after header",
            ]
        )

        segments = parse_zoom_transcript(raw_text)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "Alice")
        self.assertEqual(segments[0].text, "No blank after header")


if __name__ == "__main__":
    unittest.main()
