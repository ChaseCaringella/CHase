import unittest

from workout_tracker import calculate_set_metrics


class CalculateSetMetricsTests(unittest.TestCase):
    def test_calculates_volume_and_estimated_one_rep_max(self):
        self.assertEqual(calculate_set_metrics(100, 10), (1000, 133.33))

    def test_one_rep_set_uses_weight_as_estimated_one_rep_max(self):
        self.assertEqual(calculate_set_metrics(100, 1), (100, 100))

    def test_rejects_nonpositive_weight_or_reps(self):
        for weight, reps in ((0, 5), (100, 0)):
            with self.subTest(weight=weight, reps=reps):
                with self.assertRaises(ValueError):
                    calculate_set_metrics(weight, reps)


if __name__ == "__main__":
    unittest.main()
