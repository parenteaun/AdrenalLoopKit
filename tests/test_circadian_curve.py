#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for CircadianCurveInterpolator linear interpolation across 24 hours.
"""

from datetime import datetime, time
import unittest

from adrenalloopkit.circadian_curve import CircadianCurveInterpolator


class TestCircadianCurve(unittest.TestCase):

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
