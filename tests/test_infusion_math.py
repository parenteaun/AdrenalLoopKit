#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Hydrocortisone Infusion Math, Temp Basals, and Acute Stress Boluses.
"""

from datetime import datetime, timedelta
import unittest

from adrenalloopkit.infusion_math import (
    recommended_temp_basal,
    recommended_bolus,
    recommended_autobolus,
)


class TestInfusionMath(unittest.TestCase):

    def test_low_cortisol_increases_basal(self):
        # Scheduled rate 0.5 mg/hr, predicted cortisol dropping to 40 ng/mL, target range (100, 140)
        # Algorithm should increase rate towards max_basal_rate (2.0 mg/hr)
        rate, dur = recommended_temp_basal(
            scheduled_basal_rate=0.5,
            predicted_cortisol_dates=[datetime.now()],
            predicted_cortisol_values=[40.0],
            target_min=100.0,
            target_max=140.0,
            sensitivity=30.0,
            max_basal_rate=2.0,
        )
        self.assertTrue(rate > 0.5)
        self.assertTrue(rate <= 2.0)

    def test_high_cortisol_decreases_basal(self):
        # Scheduled rate 0.8 mg/hr, predicted cortisol elevated at 220 ng/mL, target range (100, 140)
        # Algorithm should reduce rate below 0.8 mg/hr
        rate, dur = recommended_temp_basal(
            scheduled_basal_rate=0.8,
            predicted_cortisol_dates=[datetime.now()],
            predicted_cortisol_values=[220.0],
            target_min=100.0,
            target_max=140.0,
            sensitivity=30.0,
            max_basal_rate=2.0,
        )
        self.assertTrue(rate < 0.8)
        self.assertTrue(rate >= 0.0)

    def test_crisis_threshold_triggers_acute_bolus(self):
        # Cortisol dangerously low at 22 ng/mL (nearing crisis)
        bolus, min_pred = recommended_bolus(
            predicted_cortisol_values=[22.0],
            target_min=100.0,
            target_max=140.0,
            sensitivity=30.0,
            max_bolus=5.0,
            bolus_threshold=40.0,
        )
        self.assertTrue(bolus > 0.0)
        self.assertTrue(bolus <= 5.0)


if __name__ == "__main__":
    unittest.main()
