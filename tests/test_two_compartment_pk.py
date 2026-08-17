#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Two-Compartment and Exponential PK models for hydrocortisone.
"""

import unittest
from adrenalloopkit.two_compartment_pk_model import (
    HydrocortisoneTwoCompartmentModel,
    HydrocortisoneExponentialModel,
)


class TestPharmacokinetics(unittest.TestCase):

    def test_two_compartment_decay(self):
        pk = HydrocortisoneTwoCompartmentModel(absorption_half_life=25.0, elimination_half_life=80.0, duration_of_action=300.0)
        self.assertAlmostEqual(pk.fraction_active_remaining(0), 1.0, places=3)
        self.assertAlmostEqual(pk.fraction_active_remaining(300), 0.0, places=3)
        # Monotonic decay
        frac_60 = pk.fraction_active_remaining(60)
        frac_120 = pk.fraction_active_remaining(120)
        frac_180 = pk.fraction_active_remaining(180)
        self.assertTrue(1.0 > frac_60 > frac_120 > frac_180 > 0.0)

    def test_two_compartment_activity_peak(self):
        pk = HydrocortisoneTwoCompartmentModel(absorption_half_life=25.0, elimination_half_life=80.0)
        # Check that activity rate peaks between 40 and 70 minutes
        act_10 = pk.plasma_activity_rate(10)
        act_50 = pk.plasma_activity_rate(50)
        act_150 = pk.plasma_activity_rate(150)
        self.assertTrue(act_50 > act_10)
        self.assertTrue(act_50 > act_150)

    def test_exponential_model(self):
        pk = HydrocortisoneExponentialModel(duration_minutes=300.0, peak_minutes=65.0)
        self.assertAlmostEqual(pk.fraction_active_remaining(0), 1.0, places=3)
        self.assertAlmostEqual(pk.fraction_active_remaining(300), 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
