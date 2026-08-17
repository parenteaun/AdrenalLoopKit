#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main AdrenalLoopKit Data Manager and closed-loop algorithm orchestrator.
"""

from datetime import datetime, timedelta, time
import warnings

from adrenalloopkit.models.domain_models import (
    CortisolValue,
    StressLoad,
    InfusionEntry,
    InfusionType,
    HydrocortisoneOnBoard,
    HOB,
    CircadianTargetCurve,
    HydrocortisoneSensitivity,
)
from adrenalloopkit.algorithms.circadian_curve import CircadianCurveInterpolator
from adrenalloopkit.algorithms.hydrocortisone_math import (
    hydrocortisone_on_board,
    cortisol_effects,
    reconciled,
    annotated,
    find_ratio_at_time,
)
from adrenalloopkit.storage.cortisol_store import get_recent_momentum_effects, get_counteraction_effects
from adrenalloopkit.storage.stress_store import get_stress_effects, get_stress_load_on_board
from adrenalloopkit.algorithms.infusion_math import (
    recommended_temp_basal,
    recommended_bolus,
    recommended_autobolus,
)
from adrenalloopkit.algorithms.adrenal_loop_math import predict_cortisol, decay_effect
from adrenalloopkit.utils.input_validation_tools import (
    are_settings_valid,
    are_cortisol_readings_valid,
    are_stress_readings_valid,
    are_infusion_entries_valid,
    is_hydrocortisone_sensitivity_schedule_valid,
    are_circadian_target_curves_valid,
)


def update(input_dict):
    """Executes a cycle of the AdrenalLoopKit closed-loop algorithm.

    Arguments:
        input_dict -- dictionary containing:
            "cortisol_dates" (or "glucose_dates")
            "cortisol_values" (or "glucose_values") (ng/mL)
            "infusion_types" (or "dose_types")
            "infusion_start_times" (or "dose_start_times")
            "infusion_end_times" (or "dose_end_times")
            "infusion_values" (or "dose_values") (mg or mg/hr)
            "infusion_delivered_units"
            "stress_dates" (or "carb_dates")
            "stress_values" (or "carb_values")
            "stress_absorption_times"
            "settings_dictionary"
            "hydrocortisone_sensitivity_start_times" (or "sensitivity_ratio_start_times")
            "hydrocortisone_sensitivity_end_times"
            "hydrocortisone_sensitivity_values"
            "basal_rate_start_times"
            "basal_rate_values"
            "basal_rate_minutes"
            "circadian_target_curve_start_times" (or "target_range_start_times")
            "circadian_target_curve_end_times"
            "circadian_target_curve_minimum_values"
            "circadian_target_curve_maximum_values"
            "time_to_calculate_at"

    Returns:
        recommendations dictionary with forecasted cortisol, HOB, and basal/bolus dosing.
    """
    cortisol_dates = input_dict.get("cortisol_dates") or input_dict.get("glucose_dates") or []
    cortisol_values = input_dict.get("cortisol_values") or input_dict.get("glucose_values") or []

    infusion_types = input_dict.get("infusion_types") or input_dict.get("dose_types") or []
    infusion_starts = input_dict.get("infusion_start_times") or input_dict.get("dose_start_times") or []
    infusion_ends = input_dict.get("infusion_end_times") or input_dict.get("dose_end_times") or []
    infusion_values = input_dict.get("infusion_values") or input_dict.get("dose_values") or []
    infusion_delivered = input_dict.get("infusion_delivered_units") or input_dict.get("dose_delivered_units") or []

    stress_dates = input_dict.get("stress_dates") or input_dict.get("carb_dates") or []
    stress_values = input_dict.get("stress_values") or input_dict.get("carb_values") or []
    stress_absorptions = input_dict.get("stress_absorption_times") or input_dict.get("carb_absorption_times") or []

    settings = input_dict.get("settings_dictionary") or {}

    sens_starts = input_dict.get("hydrocortisone_sensitivity_start_times") or input_dict.get("sensitivity_ratio_start_times") or [time(0, 0)]
    sens_ends = input_dict.get("hydrocortisone_sensitivity_end_times") or input_dict.get("sensitivity_ratio_end_times") or [time(23, 59)]
    sens_values = input_dict.get("hydrocortisone_sensitivity_values") or input_dict.get("sensitivity_ratio_values") or [30.0]

    basal_starts = input_dict.get("basal_rate_start_times") or [time(0, 0)]
    basal_rates = input_dict.get("basal_rate_values") or [0.5]
    basal_minutes = input_dict.get("basal_rate_minutes") or [0]

    target_starts = input_dict.get("circadian_target_curve_start_times") or input_dict.get("target_range_start_times") or [time(0, 0)]
    target_ends = input_dict.get("circadian_target_curve_end_times") or input_dict.get("target_range_end_times") or [time(23, 59)]
    target_mins = input_dict.get("circadian_target_curve_minimum_values") or input_dict.get("target_range_minimum_values") or [60.0]
    target_maxes = input_dict.get("circadian_target_curve_maximum_values") or input_dict.get("target_range_maximum_values") or [100.0]

    time_to_calculate_at = input_dict.get("time_to_calculate_at") or (cortisol_dates[-1] if cortisol_dates else datetime.now())

    # Validation
    if (
        not are_settings_valid(settings)
        or not are_cortisol_readings_valid(cortisol_dates, cortisol_values)
        or not are_stress_readings_valid(stress_dates, stress_values, stress_absorptions)
        or not are_infusion_entries_valid(infusion_types, infusion_starts, infusion_ends, infusion_values)
    ):
        return {}

    # 1. Circadian Curve Interpolation for query time
    if len(target_starts) >= 2:
        curve_interpolator = CircadianCurveInterpolator(target_starts, target_mins, target_maxes)
        current_target_min, current_target_max = curve_interpolator.target_at_time(time_to_calculate_at)
    else:
        current_target_min, current_target_max = target_mins[0], target_maxes[0]

    # 2. Reconcile Infusions & Basals
    rec_types, rec_starts, rec_ends, rec_values, rec_deliv = reconciled(
        infusion_types, infusion_starts, infusion_ends, infusion_values, infusion_delivered
    )
    scheduled_basals = annotated(
        rec_types, rec_starts, rec_ends, rec_values, rec_deliv, basal_starts, basal_rates, basal_minutes
    )

    # 3. Model Parameters
    pk_model_params = settings.get("model", [300, 80, 25])
    active_sensitivity = find_ratio_at_time(sens_starts, sens_ends, sens_values, time_to_calculate_at)

    # 4. Compute Effects
    momentum_interval = settings.get("momentum_data_interval", 15)
    mom_dates, mom_values = get_recent_momentum_effects(
        cortisol_dates, cortisol_values, momentum_data_interval=momentum_interval
    )

    hc_dates, hc_values = cortisol_effects(
        rec_types,
        rec_starts,
        rec_ends,
        rec_values,
        scheduled_basals,
        rec_deliv,
        pk_model_params,
        sens_starts,
        sens_ends,
        sens_values,
    )

    stress_dates_out, stress_values_out = get_stress_effects(
        stress_dates, stress_values, stress_absorptions
    )

    # 5. Hydrocortisone On Board (HOB) & Stress On Board (SOB)
    hob_dates, hob_values = hydrocortisone_on_board(
        rec_types,
        rec_starts,
        rec_ends,
        rec_values,
        scheduled_basals,
        rec_deliv,
        pk_model_params,
    )
    current_hob = hob_values[-1] if hob_values else 0.0
    current_sob = get_stress_load_on_board(
        stress_dates, stress_values, stress_absorptions, query_time=time_to_calculate_at
    )

    # 6. Retrospective Discrepancy Correction
    counter_starts, counter_ends, counter_values = get_counteraction_effects(
        cortisol_dates, cortisol_values, hc_dates, hc_values
    )
    retrospective_dates, retrospective_values = ([], [])
    if settings.get("retrospective_correction_enabled", True) and counter_values:
        # Sum discrepancy and decay
        cum_discrepancy = sum(counter_values[-6:]) if len(counter_values) >= 6 else sum(counter_values)
        if abs(cum_discrepancy) > 0:
            timeline = [time_to_calculate_at + timedelta(minutes=5 * i) for i in range(1, 13)]
            vals = [cum_discrepancy] * len(timeline)
            retrospective_dates, retrospective_values = decay_effect(
                timeline, vals, time_to_calculate_at, half_life_minutes=30.0
            )

    # 7. Predict Cortisol
    starting_cortisol = cortisol_values[-1] if cortisol_values else 100.0
    starting_date = cortisol_dates[-1] if cortisol_dates else time_to_calculate_at

    pred_dates, pred_values = predict_cortisol(
        starting_date=starting_date,
        starting_cortisol=starting_cortisol,
        momentum_dates=mom_dates,
        momentum_values=mom_values,
        hydrocortisone_effect_dates=hc_dates,
        hydrocortisone_effect_values=hc_values,
        stress_effect_dates=stress_dates_out,
        stress_effect_values=stress_values_out,
        correction_effect_dates=retrospective_dates,
        correction_effect_values=retrospective_values,
    )

    # 8. Basal Rate & Bolus Recommendations
    scheduled_rate = basal_rates[0] if basal_rates else 0.5
    max_basal = settings.get("max_basal_rate", 2.0)
    max_bolus = settings.get("max_bolus", 5.0)
    suspend_thresh = settings.get("suspend_threshold", 30.0)

    recommended_temp = recommended_temp_basal(
        scheduled_basal_rate=scheduled_rate,
        predicted_cortisol_dates=pred_dates,
        predicted_cortisol_values=pred_values,
        target_min=current_target_min,
        target_max=current_target_max,
        sensitivity=active_sensitivity,
        max_basal_rate=max_basal,
        suspend_threshold=suspend_thresh,
    )

    rec_bolus = recommended_bolus(
        predicted_cortisol_values=pred_values,
        target_min=current_target_min,
        target_max=current_target_max,
        sensitivity=active_sensitivity,
        current_hob=current_hob,
        max_bolus=max_bolus,
    )

    results = {
        "predicted_cortisol_dates": pred_dates,
        "predicted_cortisol_values": pred_values,
        "recommended_temp_basal": recommended_temp,
        "recommended_bolus": rec_bolus,
        "hydrocortisone_on_board": current_hob,
        "hob_timeline_dates": hob_dates,
        "hob_timeline_values": hob_values,
        "stress_load_on_board": current_sob,
        "hydrocortisone_effect_dates": hc_dates,
        "hydrocortisone_effect_values": hc_values,
        "stress_effect_dates": stress_dates_out,
        "stress_effect_values": stress_values_out,
        "momentum_effect_dates": mom_dates,
        "momentum_effect_values": mom_values,
        "current_target_min": current_target_min,
        "current_target_max": current_target_max,
        "input_data": input_dict,
    }

    return results
