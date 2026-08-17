#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cortisol rate of change, momentum effects, and counteraction effects for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
import numpy as np

from adrenalloopkit.date import time_interval_since, date_floored_to_time_interval


def linear_momentum_effect(dates, values, duration_minutes=15, delta=5):
    """Calculates short-term cortisol momentum projection via linear regression.

    Arguments:
        dates -- list of measurement datetimes
        values -- list of cortisol measurements in ng/mL
        duration_minutes -- how far forward to project momentum (default 15 mins)
        delta -- time step in minutes (default 5 mins)

    Returns:
        (momentum_dates, momentum_values)
    """
    if len(dates) < 2 or len(values) < 2:
        return ([], [])

    last_date = dates[-1]
    # Convert dates to seconds relative to first point
    t_secs = np.array([time_interval_since(d, dates[0]) for d in dates])
    y_vals = np.array(values, dtype=float)

    # Slope (ng/mL per second)
    if np.all(t_secs == t_secs[0]):
        slope = 0.0
    else:
        slope, _ = np.polyfit(t_secs, y_vals, 1)

    slope_per_min = slope * 60.0

    momentum_dates = []
    momentum_values = []

    steps = int(duration_minutes / delta)
    for i in range(1, steps + 1):
        dt = last_date + timedelta(minutes=i * delta)
        # Momentum effect decays to zero as duration is approached
        decay_factor = (steps - i + 1) / steps
        proj_effect = slope_per_min * (i * delta) * decay_factor
        momentum_dates.append(dt)
        momentum_values.append(proj_effect)

    return (momentum_dates, momentum_values)


def counteraction_effects(
    cortisol_dates,
    cortisol_values,
    infusion_effect_dates,
    infusion_effect_values,
    delta=5,
):
    """Calculates counteraction / residual disturbance effects.
    Measures the difference between observed cortisol delta and predicted hydrocortisone effect delta.
    """
    if len(cortisol_dates) < 2 or len(cortisol_values) < 2:
        return ([], [], [])

    starts = []
    ends = []
    effects = []

    for i in range(len(cortisol_dates) - 1):
        d0, d1 = cortisol_dates[i], cortisol_dates[i + 1]
        observed_delta = cortisol_values[i + 1] - cortisol_values[i]

        # Find modeled infusion delta over this window
        inf_delta = 0.0
        if infusion_effect_dates and infusion_effect_values:
            # Approximate modeled change
            try:
                idx0 = infusion_effect_dates.index(d0)
                idx1 = infusion_effect_dates.index(d1)
                inf_delta = infusion_effect_values[idx1] - infusion_effect_values[idx0]
            except ValueError:
                inf_delta = 0.0

        # Discrepancy is the counteraction / stress load disturbance
        residual = observed_delta - inf_delta
        starts.append(d0)
        ends.append(d1)
        effects.append(residual)

    return (starts, ends, effects)


# Legacy aliases
get_recent_momentum_effects = linear_momentum_effect
