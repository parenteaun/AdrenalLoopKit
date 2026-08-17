#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for CircadianTargetGenerator continuous mathematical modeling and
CircadianCurveInterpolator linear interpolation across 24 hours.
"""

from datetime import datetime, time, timedelta
import math
import unittest

from adrenalloopkit.algorithms import (
    CircadianTargetGenerator,
    generate_circadian_target_curve,
    CircadianCurveInterpolator,
)


class TestCircadianTargetGenerator(unittest.TestCase):

    def setUp(self):
        # Default generator with wake_time at 06:00
        self.generator = CircadianTargetGenerator(
            wake_time=time(6, 0),
            baseline_target=40.0,
            peak_target=180.0,
            afternoon_target=90.0,
            band_width=40.0,
            surge_exponent=2.5,
        )

    def test_morning_surge_exponential_ramp(self):
        # 3:00 AM is surge start -> baseline (40.0)
        self.assertAlmostEqual(self.generator.target_value_at(time(3, 0)), 40.0, places=1)

        # 6:00 AM is peak -> peak_target (180.0)
        self.assertAlmostEqual(self.generator.target_value_at(time(6, 0)), 180.0, places=1)

        # 4:30 AM (midpoint of surge): In exponential ramp, value should be below linear midpoint (convex curve)
        # u = 0.5, (e^(2.5*0.5)-1)/(e^2.5 - 1) = (e^1.25 - 1)/(e^2.5 - 1) ≈ 2.490 / 11.182 ≈ 0.2227
        # target ≈ 40 + 140 * 0.2227 ≈ 71.18 ng/mL (well below linear 110 ng/mL)
        surge_mid = self.generator.target_value_at(time(4, 30))
        self.assertLess(surge_mid, 110.0)
        self.assertGreater(surge_mid, 40.0)
        expected_mid = 40.0 + 140.0 * ((math.exp(1.25) - 1.0) / (math.exp(2.5) - 1.0))
        self.assertAlmostEqual(surge_mid, expected_mid, places=1)

    def test_daytime_linear_taper(self):
        # 6:00 AM (180.0) to 2:00 PM / 14:00 (90.0)
        # Midpoint at 10:00 AM should be exactly (180 + 90) / 2 = 135.0
        val_10am = self.generator.target_value_at(time(10, 0))
        self.assertAlmostEqual(val_10am, 135.0, places=1)

        # 2:00 PM (14:00) should be afternoon_target (90.0)
        val_2pm = self.generator.target_value_at(time(14, 0))
        self.assertAlmostEqual(val_2pm, 90.0, places=1)

    def test_evening_flattening_taper(self):
        # 2:00 PM / 14:00 (90.0) to 11:00 PM / 23:00 (40.0 baseline)
        val_2pm = self.generator.target_value_at(time(14, 0))
        self.assertAlmostEqual(val_2pm, 90.0, places=1)

        val_11pm = self.generator.target_value_at(time(23, 0))
        self.assertAlmostEqual(val_11pm, 40.0, places=1)

        # At 18:30 (halfway between 14:00 and 23:00, u=0.5):
        # (1 - 0.5)^2 = 0.25 -> 40 + 50 * 0.25 = 52.5 ng/mL
        val_630pm = self.generator.target_value_at(time(18, 30))
        self.assertAlmostEqual(val_630pm, 52.5, places=1)

    def test_sleep_baseline_nadir(self):
        # Between 23:00 and 03:00, target is at baseline (40.0)
        self.assertAlmostEqual(self.generator.target_value_at(time(0, 0)), 40.0, places=1)
        self.assertAlmostEqual(self.generator.target_value_at(time(1, 30)), 40.0, places=1)
        self.assertAlmostEqual(self.generator.target_value_at(time(2, 59)), 40.0, places=1)

    def test_target_at_time_range_band(self):
        # At 06:00 (center 180.0, band 40.0 -> half_band 20.0 -> [160.0, 200.0])
        min_t, max_t = self.generator.target_at_time(time(6, 0))
        self.assertEqual(min_t, 160.0)
        self.assertEqual(max_t, 200.0)

        # At midnight (center 40.0, half_band 20.0 -> [20.0, 60.0])
        min_t0, max_t0 = self.generator.target_at_time(time(0, 0))
        self.assertEqual(min_t0, 20.0)
        self.assertEqual(max_t0, 60.0)

    def test_custom_wake_time_shift(self):
        # Patient with 08:00 AM wake time:
        # Surge: 05:00 - 08:00
        # Linear taper: 08:00 - 16:00 (4:00 PM)
        # Flattening taper: 16:00 - 01:00 (1:00 AM)
        # Sleep baseline: 01:00 - 05:00
        gen_8am = CircadianTargetGenerator(wake_time=time(8, 0))

        self.assertAlmostEqual(gen_8am.target_value_at(time(5, 0)), 40.0, places=1)
        self.assertAlmostEqual(gen_8am.target_value_at(time(8, 0)), 180.0, places=1)
        self.assertAlmostEqual(gen_8am.target_value_at(time(12, 0)), 135.0, places=1)
        self.assertAlmostEqual(gen_8am.target_value_at(time(16, 0)), 90.0, places=1)
        self.assertAlmostEqual(gen_8am.target_value_at(time(1, 0)), 40.0, places=1)
        self.assertAlmostEqual(gen_8am.target_value_at(time(3, 0)), 40.0, places=1)

    def test_target_series_generation(self):
        start = datetime(2026, 8, 17, 0, 0)
        end = datetime(2026, 8, 17, 23, 55)
        dates, mins, maxs = self.generator.target_series(start, end, interval_minutes=5)
        self.assertEqual(len(dates), 288)
        self.assertEqual(len(mins), 288)
        self.assertEqual(len(maxs), 288)
        # Ensure max target is always greater than min target
        for mn, mx in zip(mins, maxs):
            self.assertGreater(mx, mn)

    def test_convenience_factory_function(self):
        gen = generate_circadian_target_curve(wake_time=time(7, 0), peak_target=200.0)
        self.assertAlmostEqual(gen.target_value_at(time(7, 0)), 200.0, places=1)


class TestCircadianCurveInterpolator(unittest.TestCase):

    def setUp(self):
        self.interpolator = CircadianCurveInterpolator.create_standard_addison_curve()

    def test_morning_peak_interpolation(self):
        # 06:00 is (120, 160), 07:30 is (160, 200)
        # At 06:45 (midpoint between 06:00 and 07:30): expected (140, 180)
        t = time(6, 45)
        min_v, max_v = self.interpolator.target_at_time(t)
        self.assertAlmostEqual(min_v, 140.0, places=1)
        self.assertAlmostEqual(max_v, 180.0, places=1)

    def test_midnight_nadir(self):
        t = time(0, 0)
        min_v, max_v = self.interpolator.target_at_time(t)
        self.assertAlmostEqual(min_v, 30.0, places=1)
        self.assertAlmostEqual(max_v, 50.0, places=1)

    def test_smooth_transition_across_midnight(self):
        t_pre = time(23, 58)
        min_pre, max_pre = self.interpolator.target_at_time(t_pre)
        t_post = time(0, 1)
        min_post, max_post = self.interpolator.target_at_time(t_post)
        self.assertAlmostEqual(min_pre, min_post, delta=1.0)


if __name__ == "__main__":
    unittest.main()
