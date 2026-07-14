import unittest

from app.ai.summarizer import limit_summary_input


class SummarizerTests(unittest.TestCase):
    def test_limit_summary_input_preserves_head_and_tail(self) -> None:
        text = "A" * 100 + "B" * 100 + "C" * 100

        limited = limit_summary_input(text, 200)

        self.assertLessEqual(len(limited), 200)
        self.assertTrue(limited.startswith("A"))
        self.assertTrue(limited.endswith("C"))
        self.assertIn("Transcript truncated", limited)

    def test_limit_summary_input_handles_non_positive_limit(self) -> None:
        self.assertEqual(limit_summary_input("hello", 0), "")


if __name__ == "__main__":
    unittest.main()
