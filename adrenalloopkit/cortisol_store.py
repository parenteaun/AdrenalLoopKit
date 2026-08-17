#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cortisol data filtering and momentum caching storage for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
from adrenalloopkit.cortisol_math import linear_momentum_effect, counteraction_effects


def get_recent_momentum_effects(cortisol_dates, cortisol_values, momentum_data_interval=15):
    """Filters recent continuous cortisol data and returns projected momentum effect."""
    if not cortisol_dates or not cortisol_values:
        return ([], [])

    now = cortisol_dates[-1]
    cutoff = now - timedelta(minutes=momentum_data_interval)

    recent_dates = [d for d in cortisol_dates if d >= cutoff]
    recent_values = [v for d, v in zip(cortisol_dates, cortisol_values) if d >= cutoff]

    return linear_momentum_effect(recent_dates, recent_values, duration_minutes=momentum_data_interval)


def get_counteraction_effects(
    cortisol_dates,
    cortisol_values,
    hydrocortisone_effect_dates,
    hydrocortisone_effect_values,
):
    """Calculates counteraction / residual disturbance timeline."""
    return counteraction_effects(
        cortisol_dates,
        cortisol_values,
        hydrocortisone_effect_dates,
        hydrocortisone_effect_values,
    )
