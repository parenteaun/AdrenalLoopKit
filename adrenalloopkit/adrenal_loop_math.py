#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core predictive mathematical algorithms and curve combination for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
import numpy as np


def predict_cortisol(
    starting_date,
    starting_cortisol,
    momentum_dates=None,
    momentum_values=None,
    hydrocortisone_effect_dates=None,
    hydrocortisone_effect_values=None,
    stress_effect_dates=None,
    stress_effect_values=None,
    correction_effect_dates=None,
    correction_effect_values=None,
    # Legacy aliases
    insulin_effect_dates=None,
    insulin_effect_values=None,
    carb_effect_dates=None,
    carb_effect_values=None,
):
    """Predicts future blood cortisol concentrations (in ng/mL) by summing:
    - Baseline starting cortisol
    - Sensor rate-of-change momentum
    - Hydrocortisone infusion elevation effect (+)
    - Biometric stress depletion / demand effect (-)
    - Retrospective discrepancy correction
    """
    if hydrocortisone_effect_dates is None and insulin_effect_dates is not None:
        hydrocortisone_effect_dates = insulin_effect_dates
        hydrocortisone_effect_values = insulin_effect_values

    if stress_effect_dates is None and carb_effect_dates is not None:
        stress_effect_dates = carb_effect_dates
        stress_effect_values = carb_effect_values

    # Determine unified forecast timeline
    all_dates = []
    if momentum_dates:
        all_dates.extend(momentum_dates)
    if hydrocortisone_effect_dates:
        all_dates.extend(hydrocortisone_effect_dates)
    if stress_effect_dates:
        all_dates.extend(stress_effect_dates)
    if correction_effect_dates:
        all_dates.extend(correction_effect_dates)

    if not all_dates:
        # 3-hour projection by default
        timeline = [starting_date + timedelta(minutes=5 * i) for i in range(1, 37)]
        return (timeline, [float(starting_cortisol)] * len(timeline))

    # Unique sorted timeline >= starting_date
    forecast_dates = sorted(list(set([d for d in all_dates if d >= starting_date])))
    if not forecast_dates:
        forecast_dates = [starting_date + timedelta(minutes=5 * i) for i in range(1, 37)]

    # Map effects by date
    mom_map = dict(zip(momentum_dates or [], momentum_values or []))
    hc_map = dict(zip(hydrocortisone_effect_dates or [], hydrocortisone_effect_values or []))
    stress_map = dict(zip(stress_effect_dates or [], stress_effect_values or []))
    corr_map = dict(zip(correction_effect_dates or [], correction_effect_values or []))

    # Baseline offsets at starting_date
    base_hc = hc_map.get(starting_date, 0.0)
    base_stress = stress_map.get(starting_date, 0.0)
    base_corr = corr_map.get(starting_date, 0.0)

    predicted_values = []
    for d in forecast_dates:
        # Mom is already relative delta
        mom = mom_map.get(d, 0.0)
        # HC delta from starting_date (positive)
        delta_hc = hc_map.get(d, base_hc) - base_hc
        # Stress delta from starting_date (negative)
        delta_stress = stress_map.get(d, base_stress) - base_stress
        # Correction delta
        delta_corr = corr_map.get(d, base_corr) - base_corr

        pred = starting_cortisol + mom + delta_hc + delta_stress + delta_corr
        predicted_values.append(max(0.0, float(pred)))

    return (forecast_dates, predicted_values)


def decay_effect(effect_dates, effect_values, start_date, half_life_minutes=30.0):
    """Linearly or exponentially decays retrospective correction discrepancy over time."""
    if not effect_dates or not effect_values:
        return ([], [])
    decayed_dates = []
    decayed_values = []
    for d, v in zip(effect_dates, effect_values):
        mins = (d - start_date).total_seconds() / 60.0
        if mins < 0:
            continue
        decay_factor = max(0.0, 1.0 - (mins / (half_life_minutes * 2.0)))
        decayed_dates.append(d)
        decayed_values.append(v * decay_factor)
    return (decayed_dates, decayed_values)


def combined_sums(dates, values):
    """Cumulative sum of values along dates."""
    return (dates, list(np.cumsum(values)))


def subtracting(dates1, values1, dates2, values2):
    """Subtracts series 2 from series 1 along matching dates."""
    val2_map = dict(zip(dates2, values2))
    out_dates = []
    out_vals = []
    for d, v in zip(dates1, values1):
        if d in val2_map:
            out_dates.append(d)
            out_vals.append(v - val2_map[d])
    return (out_dates, out_vals)


# Legacy aliases
predict_glucose = predict_cortisol
sort_dose_lists = lambda t, s, e, v: (t, s, e, v)
