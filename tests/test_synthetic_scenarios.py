#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated validation tests running synthetic 24-hour Addison's disease patient scenarios.
"""

import unittest
from tests.fixtures.AdrenalLoop.synthetic_patients import (
    generate_normal_24h_scenario,
    generate_acute_stress_scenario,
    generate_illness_infection_scenario,
    generate_near_crisis_scenario,
)
from adrenalloopkit.manager import update


class TestSyntheticAddisonScenarios(unittest.TestCase):

    def test_normal_24h_scenario(self):
        scenario = generate_normal_24h_scenario()
        output = update(scenario)
        self.assertIsNotNone(output)
        self.assertTrue(len(output["predicted_cortisol_values"]) > 0)
        # Recommended basal should stay close to scheduled basal
        rate, dur = output["recommended_temp_basal"]
        self.assertTrue(0.0 <= rate <= 2.0)

    def test_acute_workout_stress_scenario(self):
        scenario = generate_acute_stress_scenario()
        output = update(scenario)
        self.assertIsNotNone(output)
        self.assertTrue(output["stress_load_on_board"] > 0)
        # Stress effects should be populated and negative
        self.assertTrue(len(output["stress_effect_values"]) > 0)
        self.assertTrue(any(v < 0 for v in output["stress_effect_values"]))

    def test_prolonged_illness_scenario(self):
        scenario = generate_illness_infection_scenario()
        output = update(scenario)
        self.assertIsNotNone(output)
        self.assertTrue(output["stress_load_on_board"] > 50)
        # Prolonged illness demand causes downward pressure on cortisol, elevating temp basal
        rate, dur = output["recommended_temp_basal"]
        self.assertTrue(rate >= 0.5)

    def test_near_crisis_scenario(self):
        scenario = generate_near_crisis_scenario()
        output = update(scenario)
        self.assertIsNotNone(output)
        # Critical low cortisol should trigger an acute bolus recommendation or rate escalation
        bolus, min_pred = output["recommended_bolus"]
        rate, dur = output["recommended_temp_basal"]
        self.assertTrue(bolus > 0.0 or rate > 0.5)


if __name__ == "__main__":
    unittest.main()
