#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for AdrenalLoopKit domain models.
"""

from datetime import datetime, time
import unittest

from adrenalloopkit.domain_models import (
    CortisolValue,
    StressLoad,
    InfusionEntry,
    InfusionType,
    HydrocortisoneOnBoard,
    HOB,
    CircadianTargetCurve,
    HydrocortisoneSensitivity,
)


class TestDomainModels(unittest.TestCase):

    def test_cortisol_value(self):
        now = datetime(2026, 8, 17, 8, 0)
        cv = CortisolValue(date=now, value=125.4, provenance="sensor_01")
        self.assertEqual(cv.date, now)
        self.assertEqual(cv.value, 125.4)
        self.assertEqual(cv.provenance, "sensor_01")

    def test_stress_load(self):
        now = datetime(2026, 8, 17, 14, 0)
        sl = StressLoad(date=now, value=50, absorption_time=120.0, stress_type="acute")
        self.assertEqual(sl.value, 50)
        self.assertEqual(sl.absorption_time, 120.0)
        self.assertEqual(sl.stress_type, "acute")

    def test_infusion_entry(self):
        start = datetime(2026, 8, 17, 8, 0)
        end = datetime(2026, 8, 17, 8, 30)
        ie = InfusionEntry(
            type=InfusionType.tempbasal,
            start_time=start,
            end_time=end,
            value=1.5,
            delivered_units=0.75,
        )
        self.assertEqual(ie.type, InfusionType.tempbasal)
        self.assertEqual(ie.value, 1.5)
        self.assertEqual(ie.delivered_units, 0.75)

    def test_hydrocortisone_on_board(self):
        now = datetime(2026, 8, 17, 12, 0)
        hob = HydrocortisoneOnBoard(date=now, value=2.4)
        self.assertEqual(hob.value, 2.4)
        h = HOB(date=now, value=3.0)
        self.assertEqual(h.value, 3.0)

    def test_circadian_target_curve(self):
        t0 = time(6, 0)
        t1 = time(8, 0)
        curve = CircadianTargetCurve(start_time=t0, end_time=t1, min_cortisol=120.0, max_cortisol=160.0)
        self.assertEqual(curve.min_cortisol, 120.0)
        self.assertEqual(curve.max_cortisol, 160.0)

    def test_hydrocortisone_sensitivity(self):
        t0 = time(0, 0)
        t1 = time(23, 59)
        sens = HydrocortisoneSensitivity(start_time=t0, end_time=t1, value=28.5)
        self.assertEqual(sens.value, 28.5)


if __name__ == "__main__":
    unittest.main()
