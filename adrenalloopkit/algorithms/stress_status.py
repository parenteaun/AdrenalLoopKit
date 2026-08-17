#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress status and active stress demand dynamics for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
import math


def dynamic_stress_demand_remaining(time_since_onset_minutes, absorption_time_minutes=180.0, stress_type="acute"):
    """Returns the fraction of uncompensated stress demand remaining at time t.

    - Acute physical stress: Fast onset and exponential decay recovery.
    - Illness / infection: Prolonged sustained demand plateau before decay.
    """
    if time_since_onset_minutes <= 0:
        return 1.0
    if time_since_onset_minutes >= absorption_time_minutes:
        return 0.0

    t = time_since_onset_minutes
    dur = absorption_time_minutes

    if stress_type == "acute":
        # Exponential decay: e^(-2.5 * t / dur) normalized
        decay = math.exp(-2.5 * t / dur) - math.exp(-2.5)
        scale = 1.0 - math.exp(-2.5)
        return max(0.0, min(1.0, decay / scale))
    else:
        # Prolonged illness: sustained plateau for 50% of duration, then decay
        half = dur * 0.5
        if t <= half:
            return 1.0
        else:
            return max(0.0, (dur - t) / (dur - half))
