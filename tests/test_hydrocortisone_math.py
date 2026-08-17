#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Hydrocortisone Math, HOB tracking, and Cortisol Elevation Effects.
"""

from datetime import datetime, timedelta, time
import unittest

from adrenalloopkit.models import InfusionType
from adrenalloopkit.algorithms import (
    hydrocortisone_on_board,
    cortisol_effects,
    reconciled,
    annotated,
)


class TestHydrocortisoneMath(unittest.TestCase):

    def test_cortisol_elevation_effect_is_positive(self):
        # 2 mg bolus with sensitivity 30 ng/mL/mg should raise cortisol by up to 60 ng/mL
        now = datetime(2026, 8, 17, 8, 0)
        types = [InfusionType.bolus]
        starts = [now]
        ends = [now + timedelta(minutes=5)]
        values = [2.0]
        scheduled_basals = [0.0]
        delivered = [2.0]

        dates, effects = cortisol_effects(
            types, starts, ends, values, scheduled_basals, delivered,
            model_params=[300, 80, 25],
            sensitivities_starts=[time(0, 0)],
            sensitivities_ends=[time(23, 59)],
            sensitivities_values=[30.0],
            delay=0,
        )

        self.assertTrue(len(effects) > 0)
        # Check that effect rises over time and is strictly positive
        self.assertTrue(effects[0] >= 0.0)
        self.assertTrue(effects[-1] > effects[0])
        self.assertAlmostEqual(effects[-1], 60.0, delta=2.0)

    def test_hydrocortisone_on_board_decay(self):
        now = datetime(2026, 8, 17, 8, 0)
        types = [InfusionType.bolus]
        starts = [now]
        ends = [now + timedelta(minutes=5)]
        values = [2.0]
        scheduled_basals = [0.0]
        delivered = [2.0]

        dates, hobs = hydrocortisone_on_board(
            types, starts, ends, values, scheduled_basals, delivered,
            model_params=[300, 80, 25],
            delay=0,
        )

        self.assertTrue(len(hobs) > 0)
        self.assertAlmostEqual(hobs[0], 2.0, places=1)
        self.assertAlmostEqual(hobs[-1], 0.0, places=1)


if __name__ == "__main__":
    unittest.main()
