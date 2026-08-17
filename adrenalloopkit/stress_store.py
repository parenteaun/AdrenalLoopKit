#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress event storage, filtering, and timeline querying for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
from adrenalloopkit.stress_math import stress_effects, stress_load_on_board


def get_stress_effects(
    stress_dates,
    stress_values,
    stress_absorption_times,
    start_date=None,
    end_date=None,
    delta=5,
):
    """Calculates stress effect timeline."""
    return stress_effects(
        stress_dates,
        stress_values,
        stress_absorption_times,
        start=start_date,
        end=end_date,
        delta=delta,
    )


def get_stress_load_on_board(
    stress_dates,
    stress_values,
    stress_absorption_times,
    query_time=None,
):
    """Calculates active stress load on board."""
    return stress_load_on_board(
        stress_dates,
        stress_values,
        stress_absorption_times,
        query_time=query_time,
    )


# Legacy aliases
get_carb_glucose_effects = get_stress_effects
get_carbs_on_board = get_stress_load_on_board
