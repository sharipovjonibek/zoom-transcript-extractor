import unittest

from app.utils.time_utils import (
    canonical_time,
    is_valid_time_format,
    is_valid_time_range,
    segment_overlaps_requested_range,
)


class TimeUtilsTests(unittest.TestCase):
    def test_validates_and_canonicalizes_duration_style_times(self) -> None:
        self.assertTrue(is_valid_time_format("1:02"))
        self.assertTrue(is_valid_time_format("25:00"))
        self.assertFalse(is_valid_time_format("1:99"))
        self.assertEqual(canonical_time("1:02"), "01:02")

    def test_validates_time_range_order(self) -> None:
        self.assertTrue(is_valid_time_range("01:00", "01:00"))
        self.assertTrue(is_valid_time_range("01:00", "01:30"))
        self.assertFalse(is_valid_time_range("01:30", "01:00"))

    def test_segment_overlap_includes_boundary(self) -> None:
        self.assertTrue(
            segment_overlaps_requested_range("01:00", "02:00", "02:00", "03:00")
        )


if __name__ == "__main__":
    unittest.main()
