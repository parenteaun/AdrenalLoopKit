#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for AdrenalDataManager update() orchestration.
"""

from datetime import datetime, timedelta, time
import unittest

from adrenalloopkit.models import InfusionType
from adrenalloopkit.manager import update


class TestAdrenalDataManager(unittest.TestCase):

    def test_update_orchestration(self):
        now = datetime(2026, 8, 17, 8, 0)
        input_dict = {
            "cortisol_dates": [now - timedelta(minutes=15), now - timedelta(minutes=10), now - timedelta(minutes=5), now],
            "cortisol_values": [120.0, 125.0, 130.0, 135.0],
            "infusion_types": [InfusionType.basal],
            "infusion_start_times": [now - timedelta(hours=4)],
            "infusion_end_times": [now],
            "infusion_values": [0.6],
            "infusion_delivered_units": [2.4],
            "stress_dates": [],
            "stress_values": [],
            "stress_absorption_times": [],
            "settings_dictionary": {
                "model": [300, 80, 25],
                "momentum_data_interval": 15,
                "suspend_threshold": 30.0,
                "max_basal_rate": 2.0,
                "max_bolus": 5.0,
            },
            "hydrocortisone_sensitivity_start_times": [time(0, 0)],
            "hydrocortisone_sensitivity_end_times": [time(23, 59)],
            "hydrocortisone_sensitivity_values": [30.0],
            "basal_rate_start_times": [time(0, 0)],
            "basal_rate_values": [0.6],
            "basal_rate_minutes": [0],
            "circadian_target_curve_start_times": [time(0, 0), time(8, 0), time(23, 59)],
            "circadian_target_curve_end_times": [time(8, 0), time(23, 59), time(23, 59)],
            "circadian_target_curve_minimum_values": [40.0, 140.0, 40.0],
            "circadian_target_curve_maximum_values": [60.0, 180.0, 60.0],
            "time_to_calculate_at": now,
        }

        output = update(input_dict)
        self.assertIsNotNone(output)
        self.assertIn("predicted_cortisol_dates", output)
        self.assertIn("predicted_cortisol_values", output)
        self.assertIn("recommended_temp_basal", output)
        self.assertIn("recommended_bolus", output)
        self.assertIn("hydrocortisone_on_board", output)
        self.assertEqual(len(output["predicted_cortisol_dates"]), len(output["predicted_cortisol_values"]))


if __name__ == "__main__":
    unittest.main()
