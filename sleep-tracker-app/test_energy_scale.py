import unittest

from energy_scale import describe_energy_level


class DescribeEnergyLevelTests(unittest.TestCase):
    def test_describes_each_energy_band_at_its_boundaries(self):
        expected = {
            1: "Extremely low (1-9)",
            9: "Extremely low (1-9)",
            10: "Very low (10-29)",
            29: "Very low (10-29)",
            30: "Low (30-49)",
            49: "Low (30-49)",
            50: "Moderate (50-69)",
            69: "Moderate (50-69)",
            70: "High (70-89)",
            89: "High (70-89)",
            90: "Peak (90-100)",
            100: "Peak (90-100)",
        }

        for level, expected_label in expected.items():
            with self.subTest(level=level):
                label, description = describe_energy_level(level)
                self.assertEqual(label, expected_label)
                self.assertTrue(description)

    def test_rejects_values_outside_the_scale(self):
        for level in (0, 101):
            with self.subTest(level=level):
                with self.assertRaises(ValueError):
                    describe_energy_level(level)


if __name__ == "__main__":
    unittest.main()
