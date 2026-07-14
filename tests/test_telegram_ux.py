import unittest

from app.handlers.extract_flow import is_cancel_text, is_skip_text
from app.keyboards.cancel_keyboard import CANCEL_BUTTON, SKIP_BUTTON, cancel_keyboard, time_filter_keyboard
from app.keyboards.main_menu_keyboard import HELP_BUTTON, NEW_TRANSCRIPT_BUTTON, get_main_menu_keyboard
from app.keyboards.summary_keyboard import build_summary_keyboard


class TelegramUxTests(unittest.TestCase):
    def test_main_menu_has_primary_action_and_help(self) -> None:
        keyboard = get_main_menu_keyboard()

        self.assertEqual(keyboard.keyboard[0][0].text, NEW_TRANSCRIPT_BUTTON)
        self.assertEqual(keyboard.keyboard[1][0].text, HELP_BUTTON)

    def test_time_filter_keyboard_has_skip_and_cancel(self) -> None:
        keyboard = time_filter_keyboard()

        self.assertEqual(keyboard.keyboard[0][0].text, SKIP_BUTTON)
        self.assertEqual(keyboard.keyboard[0][1].text, CANCEL_BUTTON)

    def test_cancel_keyboard_has_only_cancel(self) -> None:
        keyboard = cancel_keyboard()

        self.assertEqual(len(keyboard.keyboard), 1)
        self.assertEqual(keyboard.keyboard[0][0].text, CANCEL_BUTTON)

    def test_summary_keyboard_uses_clear_final_actions(self) -> None:
        keyboard = build_summary_keyboard()

        self.assertEqual(keyboard.inline_keyboard[0][0].text, "🧠 Generate Summary")
        self.assertEqual(keyboard.inline_keyboard[1][0].text, "✅ Finish Without Summary")

    def test_skip_and_cancel_text_helpers_accept_buttons_and_typed_skip(self) -> None:
        self.assertTrue(is_skip_text(SKIP_BUTTON))
        self.assertTrue(is_skip_text("skip"))
        self.assertTrue(is_skip_text("SKIP"))
        self.assertTrue(is_cancel_text(CANCEL_BUTTON))
        self.assertFalse(is_skip_text(CANCEL_BUTTON))


if __name__ == "__main__":
    unittest.main()
