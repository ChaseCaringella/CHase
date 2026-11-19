import unittest

from sleep_scoring import calculate_sleep_score, get_sleep_coaching_tip


class CalculateSleepScoreTests(unittest.TestCase):
    def test_full_points_at_adult_duration_and_efficiency_targets(self):
        score, breakdown = calculate_sleep_score(
            time_in_bed_mins=500,
            sleep_latency_mins=20,
            awake_after_sleep_mins=55,
            restfulness=10,
        )

        self.assertEqual(score, 100)
        self.assertEqual(sum(breakdown.values()), score)

    def test_short_sleep_and_low_restfulness_reduce_score(self):
        score, breakdown = calculate_sleep_score(
            time_in_bed_mins=480,
            sleep_latency_mins=40,
            awake_after_sleep_mins=80,
            restfulness=5,
        )

        self.assertLess(score, 80)
        self.assertLess(breakdown["Duration"], 35)
        self.assertLess(breakdown["Time to fall asleep"], 15)

    def test_rejects_awake_time_that_exceeds_time_in_bed(self):
        with self.assertRaises(ValueError):
            calculate_sleep_score(
                time_in_bed_mins=300,
                sleep_latency_mins=120,
                awake_after_sleep_mins=181,
                restfulness=5,
            )

    def test_coaching_tip_focuses_on_lowest_scoring_component(self):
        tip = get_sleep_coaching_tip(
            55,
            {
                "Duration": 35,
                "Sleep efficiency": 10,
                "Time to fall asleep": 5,
                "Restfulness": 5,
            },
        )

        self.assertIn("wind-down routine", tip)


if __name__ == "__main__":
    unittest.main()
