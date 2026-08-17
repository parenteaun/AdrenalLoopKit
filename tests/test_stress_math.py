#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Stress Load Math and Dynamic Recovery Curves.
"""

from datetime import datetime, timedelta
import unittest

from adrenalloopkit.stress_status import dynamic_stress_demand_remaining
from adrenalloopkit.stress_math import stress_effects, stress_load_on_board


class TestStressMath(unittest.TestCase):

    def test_dynamic_stress_decay_acute(self):
        # Acute stress decays quickly
        f0 = dynamic_stress_demand_remaining(0, 180.0, "acute")
        f60 = dynamic_stress_demand_remaining(60, 180.0, "acute")
        f180 = dynamic_stress_demand_remaining(180, 180.0, "acute")
        self.assertAlmostEqual(f0, 1.0, places=2)
        self.assertTrue(f60 < f0)
        self.assertAlmostEqual(f180, 0.0, places=2)

    def test_dynamic_stress_decay_illness(self):
        # Illness sustains demand plateau for first half of duration
        f0 = dynamic_stress_demand_remaining(0, 360.0, "illness")
        f120 = dynamic_stress_demand_remaining(120, 360.0, "illness")
        f360 = dynamic_stress_demand_remaining(360, 360.0, "illness")
        self.assertEqual(f0, 1.0)
        self.assertEqual(f120, 1.0)
        self.assertAlmostEqual(f360, 0.0, places=2)

    def test_stress_effects_negative_disturbance(self):
        now = datetime(2026, 8, 17, 14, 0)
        dates, effects = stress_effects(
            stress_dates=[now],
            stress_values=[50],
            stress_absorption_times=[120.0],
            stress_sensitivity_multiplier=1.0,
        )
        self.assertTrue(len(effects) > 0)
        # All stress effects are negative demand disturbances on cortisol balance
        self.assertTrue(all(v <= 0.0 for v in effects))


if __name__ == "__main__":
    unittest.main()
