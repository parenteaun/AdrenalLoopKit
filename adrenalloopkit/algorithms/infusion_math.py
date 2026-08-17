#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrocortisone infusion rate calculations, recommended temporary basal rates,
and acute stress bolus recommendations for AdrenalLoopKit.
"""

from datetime import datetime, timedelta, time
import numpy as np
from enum import Enum

from adrenalloopkit.models.domain_models import InfusionType


class Correction(Enum):
    in_range = "in_range"
    above_range = "above_range"
    below_range = "below_range"


def recommended_temp_basal(
    scheduled_basal_rate,
    predicted_cortisol_dates,
    predicted_cortisol_values,
    target_min,
    target_max,
    sensitivity,
    max_basal_rate=2.0,
    suspend_threshold=30.0,
    rate_rounder=0.05,
    temp_duration_minutes=30,
):
    """Calculates recommended temporary hydrocortisone basal rate (mg/hr).

    In Addison's disease:
    - If predicted cortisol is below target_min: Increase basal rate (up to max_basal_rate) to restore cortisol.
    - If predicted cortisol is dangerously high (above target_max): Decrease basal rate (down to 0.0 mg/hr).
    - If predicted cortisol is below suspend_threshold (crisis risk): Do NOT suspend; ensure positive infusion!

    Arguments:
        scheduled_basal_rate -- baseline scheduled rate in mg/hr
        predicted_cortisol_dates -- list of forecasted datetimes
        predicted_cortisol_values -- list of forecasted cortisol levels in ng/mL
        target_min -- target cortisol lower bound in ng/mL
        target_max -- target cortisol upper bound in ng/mL
        sensitivity -- ng/mL rise per 1 mg hydrocortisone
        max_basal_rate -- maximum allowed rate in mg/hr (default: 2.0 mg/hr)
        suspend_threshold -- critical threshold in ng/mL
        rate_rounder -- pump resolution (e.g. 0.05 mg/hr)
        temp_duration_minutes -- temp basal duration in minutes (default 30 min)

    Returns:
        (rate_mg_per_hr, duration_mins)
    """
    if not predicted_cortisol_values:
        return (scheduled_basal_rate, temp_duration_minutes)

    # Evaluate eventual predicted cortisol (at end of prediction horizon ~2-3 hrs)
    eventual_cortisol = predicted_cortisol_values[-1]
    min_predicted = min(predicted_cortisol_values)

    target_center = (target_min + target_max) / 2.0
    cortisol_deficit = target_center - eventual_cortisol  # positive if cortisol is too low!

    if sensitivity <= 0:
        sensitivity = 30.0

    # Hydrocortisone needed (mg) over the DIA horizon (~4 hours = 4.0 hrs)
    horizon_hours = 3.0
    mg_needed = cortisol_deficit / sensitivity

    # Required rate adjustment (mg/hr)
    rate_adjustment = mg_needed / horizon_hours
    target_rate = scheduled_basal_rate + rate_adjustment

    # Enforce software safety bounds
    target_rate = max(0.0, min(max_basal_rate, target_rate))

    # Round to pump increment
    rounded_rate = round(target_rate / rate_rounder) * rate_rounder

    # If within nominal threshold of scheduled rate, keep scheduled rate
    if abs(rounded_rate - scheduled_basal_rate) < rate_rounder:
        rounded_rate = scheduled_basal_rate

    return (round(rounded_rate, 3), temp_duration_minutes)


def recommended_bolus(
    predicted_cortisol_values,
    target_min,
    target_max,
    sensitivity,
    current_hob=0.0,
    max_bolus=5.0,
    bolus_threshold=40.0,
):
    """Calculates acute stress bolus recommendation in mg.

    Used when cortisol is acutely deficient (e.g. nearing crisis < 40 ng/mL)
    or during acute biometric stress events.
    """
    if not predicted_cortisol_values:
        return (0.0, 0.0)

    min_predicted = min(predicted_cortisol_values)
    target_center = (target_min + target_max) / 2.0

    # Only recommend bolus if predicted cortisol drops significantly below target
    if min_predicted < bolus_threshold:
        deficit = target_center - min_predicted
        needed_mg = deficit / (sensitivity if sensitivity > 0 else 30.0)
        # Deduct active HOB already circulating
        net_bolus = max(0.0, needed_mg - current_hob)
        bounded_bolus = min(max_bolus, net_bolus)
        return (round(bounded_bolus, 2), min_predicted)

    return (0.0, min_predicted)


def recommended_autobolus(
    predicted_cortisol_values,
    target_min,
    target_max,
    sensitivity,
    current_hob=0.0,
    max_bolus=2.0,
    partial_application_factor=0.2,
):
    """Calculates micro-bolus adjustment (autobolus) in mg."""
    full_bolus, min_pred = recommended_bolus(
        predicted_cortisol_values, target_min, target_max, sensitivity, current_hob, max_bolus
    )
    auto_dose = full_bolus * partial_application_factor
    return round(max(0.0, min(max_bolus, auto_dose)), 3)
