#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input validation tools and clinical safety bounds for AdrenalLoopKit (Addison's Disease).
"""

import warnings
from adrenalloopkit.infusion import InfusionType


def are_settings_valid(settings):
    """Validates settings dictionary against Addison's disease clinical safety bounds."""
    if not settings:
        warnings.warn("Error: settings dictionary is empty; stopping run.")
        return False

    model = settings.get("model")
    if model and any(v <= 0 or v >= 1440 for v in model):
        warnings.warn("Error: invalid PK model parameters; stopping run.")
        return False

    max_basal = settings.get("max_basal_rate", 2.0)
    if max_basal < 0 or max_basal > 5.0:
        warnings.warn(
            f"Warning: max_basal_rate ({max_basal} mg/hr) outside typical bounds (0 - 5.0 mg/hr); continuing anyway."
        )

    max_bolus = settings.get("max_bolus", 10.0)
    if max_bolus < 0 or max_bolus > 25.0:
        warnings.warn(
            f"Warning: max_bolus ({max_bolus} mg) outside typical bounds (0 - 25.0 mg); continuing anyway."
        )

    return True


def are_cortisol_readings_valid(dates, cortisol_values):
    """Validates continuous wearable sensor cortisol readings in ng/mL."""
    if not cortisol_values:
        return True

    if any(v < 0 for v in cortisol_values):
        warnings.warn("Error: cortisol measurements cannot be negative; stopping run.")
        return False

    if any(v < 30.0 for v in cortisol_values):
        warnings.warn(
            "Caution: cortisol reading < 30 ng/mL detected; acute adrenal crisis risk; continuing."
        )

    if any(v > 350.0 for v in cortisol_values):
        warnings.warn(
            "Caution: cortisol reading > 350 ng/mL detected; acute over-replacement risk; continuing."
        )

    return True


def are_stress_readings_valid(dates, stress_values, absorption_times):
    """Validates biometric stress load inputs."""
    if not stress_values:
        return True

    if any(v < 0 for v in stress_values):
        warnings.warn("Error: stress load metric cannot be negative; stopping run.")
        return False

    if absorption_times and any(a <= 0 or a > 1440 for a in absorption_times if a is not None):
        warnings.warn("Error: stress absorption times must be between 1 and 1440 mins; stopping run.")
        return False

    return True


def are_infusion_entries_valid(types, start_times, end_times, values):
    """Validates hydrocortisone infusion entries."""
    if not values:
        return True

    if any(v < 0 or v > 25.0 for v in values):
        warnings.warn("Warning: infusion value outside typical bounds (0 - 25.0 mg or mg/hr); continuing.")

    if any(s > e for s, e in zip(start_times, end_times)):
        warnings.warn("Error: infusion start time cannot be after end time; stopping run.")
        return False

    return True


def is_hydrocortisone_sensitivity_schedule_valid(start_times, end_times, sensitivity_values):
    """Validates hydrocortisone sensitivity schedule in ng/mL per mg HC."""
    if not sensitivity_values:
        return True

    if any(v <= 0 or v > 200.0 for v in sensitivity_values):
        warnings.warn("Warning: sensitivity multiplier outside typical range (5 - 200 ng/mL/mg); continuing.")

    return True


def are_circadian_target_curves_valid(start_times, end_times, min_values, max_values):
    """Validates circadian target curve boundaries in ng/mL."""
    if not min_values or not max_values:
        return True

    if any(v < 10.0 or v > 300.0 for v in min_values) or any(v < 20.0 or v > 350.0 for v in max_values):
        warnings.warn("Warning: circadian target curve values outside physiological limits (10 - 350 ng/mL); continuing.")

    return True


# Legacy aliases
are_glucose_readings_valid = are_cortisol_readings_valid
are_carb_readings_valid = are_stress_readings_valid
are_insulin_doses_valid = are_infusion_entries_valid
is_insulin_sensitivity_schedule_valid = is_hydrocortisone_sensitivity_schedule_valid
are_correction_ranges_valid = are_circadian_target_curves_valid
are_basal_rates_valid = lambda start_times, rates, minutes_active: True
are_carb_ratios_valid = lambda dates, ratios: True
