#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress demand math, stress depletion modeling, and stress-on-board calculations.
"""

from datetime import datetime, timedelta
import numpy as np

from adrenalloopkit.date import time_interval_since, date_floored_to_time_interval
from adrenalloopkit.stress_status import dynamic_stress_demand_remaining


def stress_effects(
    stress_dates,
    stress_values,
    stress_absorption_times,
    stress_types=None,
    stress_sensitivity_multiplier=1.0,
    start=None,
    end=None,
    delta=5,
):
    """Calculates downward cortisol disturbance / demand effects from biometric stress events.

    In Addison's disease, acute or prolonged stress creates an active demand
    depleting circulating cortisol if not compensated by hydrocortisone.

    Arguments:
        stress_dates -- list of start datetimes for stress events
        stress_values -- list of integer/float stress load metrics
        stress_absorption_times -- list of duration in minutes
        stress_types -- list of 'acute' or 'illness'
        stress_sensitivity_multiplier -- scale factor for ng/mL demand per stress unit
        start -- timeline start datetime
        end -- timeline end datetime
        delta -- timeline step in minutes

    Returns:
        (effect_dates, effect_values) in ng/mL equivalent demand
    """
    if not stress_dates or not stress_values:
        return ([], [])

    if stress_types is None:
        stress_types = ["acute"] * len(stress_dates)

    max_dur = max(stress_absorption_times) if stress_absorption_times else 180.0
    if start is None:
        start = date_floored_to_time_interval(min(stress_dates), delta)
    if end is None:
        end = date_floored_to_time_interval(max(stress_dates) + timedelta(minutes=max_dur), delta)

    if start > end:
        return ([], [])

    effect_dates = []
    effect_values = []

    curr_date = start
    while curr_date <= end:
        cum_effect = 0.0
        for i in range(len(stress_dates)):
            s_date = stress_dates[i]
            s_val = stress_values[i]
            s_dur = stress_absorption_times[i] if stress_absorption_times[i] else 180.0
            s_type = stress_types[i] if i < len(stress_types) else "acute"

            mins_since = time_interval_since(curr_date, s_date) / 60.0
            if mins_since <= 0:
                frac_demanded = 0.0
            elif mins_since >= s_dur:
                frac_demanded = 1.0
            else:
                frac_demanded = 1.0 - dynamic_stress_demand_remaining(mins_since, s_dur, s_type)

            # Cumulative stress disturbance (downward demand)
            cum_effect += s_val * stress_sensitivity_multiplier * frac_demanded

        effect_dates.append(curr_date)
        effect_values.append(-cum_effect)  # Negative effect on cortisol balance
        curr_date += timedelta(minutes=delta)

    return (effect_dates, effect_values)


def stress_load_on_board(
    stress_dates,
    stress_values,
    stress_absorption_times,
    stress_types=None,
    query_time=None,
):
    """Calculates active uncompensated stress load remaining at query_time."""
    if not stress_dates or not stress_values:
        return 0.0

    if query_time is None:
        query_time = stress_dates[-1]

    if stress_types is None:
        stress_types = ["acute"] * len(stress_dates)

    total_active_stress = 0.0
    for i in range(len(stress_dates)):
        s_date = stress_dates[i]
        s_val = stress_values[i]
        s_dur = stress_absorption_times[i] if stress_absorption_times[i] else 180.0
        s_type = stress_types[i] if i < len(stress_types) else "acute"

        mins_since = time_interval_since(query_time, s_date) / 60.0
        if 0 <= mins_since < s_dur:
            frac = dynamic_stress_demand_remaining(mins_since, s_dur, s_type)
            total_active_stress += s_val * frac

    return total_active_stress


# Legacy aliases
carb_glucose_effects = stress_effects
dynamic_glucose_effects = stress_effects
get_carbs_on_board = stress_load_on_board
