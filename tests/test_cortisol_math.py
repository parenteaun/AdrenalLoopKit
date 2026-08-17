#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Cortisol Math, Linear Momentum, and Counteraction Effects.
"""

from datetime import datetime, timedelta
import unittest

from adrenalloopkit.algorithms.cortisol_math import linear_momentum_effect, counteraction_effects


class TestCortisolMath(unittest.TestCase):

    def test_rising_momentum(self):
        now = datetime(2026, 8, 17, 8, 0)
        dates = [now - timedelta(minutes=15), now - timedelta(minutes=10), now - timedelta(minutes=5), now]
        # Cortisol rising from 100 to 130
        values = [100.0, 110.0, 120.0, 130.0]

        mom_dates, mom_values = linear_momentum_effect(dates, values, duration_minutes=15, delta=5)
        self.assertEqual(len(mom_dates), 3)
        # Rising momentum should be strictly positive
        self.assertTrue(all(v > 0 for v in mom_values))

    def test_falling_momentum(self):
        now = datetime(2026, 8, 17, 8, 0)
        dates = [now - timedelta(minutes=15), now - timedelta(minutes=10), now - timedelta(minutes=5), now]
        # Cortisol falling from 130 to 100
        values = [130.0, 120.0, 110.0, 100.0]

        mom_dates, mom_values = linear_momentum_effect(dates, values, duration_minutes=15, delta=5)
        self.assertEqual(len(mom_dates), 3)
        # Falling momentum should be strictly negative
        self.assertTrue(all(v < 0 for v in mom_values))


if __name__ == "__main__":
    unittest.main()
