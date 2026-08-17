#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrocortisone infusion pharmacokinetics, Hydrocortisone-On-Board (HOB),
and blood cortisol elevation effect calculations.
"""

from datetime import datetime, timedelta, time
import math
import numpy as np

from adrenalloopkit.infusion import InfusionType, DoseType
from adrenalloopkit.infusion_entry import net_infusion_units, total_infusion_units, hours
from adrenalloopkit.date import time_interval_since, date_floored_to_time_interval
from adrenalloopkit.two_compartment_pk_model import (
    HydrocortisoneTwoCompartmentModel,
    HydrocortisoneExponentialModel,
)


def get_pk_model(model_params):
    """Instantiates the appropriate PK model.
    model_params can be:
    - [DIA]: 1-compartment, peak default 65 mins
    - [DIA, peak]: 1-compartment exponential
    - [DIA, peak, ka_half_life]: 2-compartment model
    """
    if not model_params:
        return HydrocortisoneTwoCompartmentModel()
    if len(model_params) == 1:
        return HydrocortisoneTwoCompartmentModel(duration_of_action=model_params[0] * 60 if model_params[0] <= 24 else model_params[0])
    elif len(model_params) == 2:
        return HydrocortisoneExponentialModel(duration_minutes=model_params[0], peak_minutes=model_params[1])
    else:
        return HydrocortisoneTwoCompartmentModel(
            duration_of_action=model_params[0],
            elimination_half_life=model_params[1],
            absorption_half_life=model_params[2],
        )


def simulation_date_range_for_samples(start_times, end_times, duration, delay=10, delta=5):
    """Determines start and end dates for simulation timeline."""
    if not start_times:
        return (None, None)
    min_start = min(start_times) + timedelta(minutes=delay)
    max_end = max(end_times) + timedelta(minutes=duration + delay)
    start_floored = date_floored_to_time_interval(min_start, delta)
    end_floored = date_floored_to_time_interval(max_end, delta)
    return (start_floored, end_floored)


def hydrocortisone_on_board(
    infusion_types,
    start_dates,
    end_dates,
    values,
    scheduled_basal_rates,
    delivered_units,
    model_params,
    start=None,
    end=None,
    delay=10,
    delta=5,
):
    """Calculates active hydrocortisone on board (HOB) timeline across doses.

    Returns:
        (hob_dates, hob_values) where hob_values are in mg.
    """
    if not infusion_types:
        return ([], [])

    pk_model = get_pk_model(model_params)
    dia_mins = pk_model.dia

    if start is None or end is None:
        start, end = simulation_date_range_for_samples(
            start_dates, end_dates, dia_mins, delay, delta
        )

    if start is None or end is None or start > end:
        return ([], [])

    hob_dates = []
    hob_values = []

    curr_date = start
    while curr_date <= end:
        hob_sum = 0.0
        for i in range(len(infusion_types)):
            # Net dose in mg
            net_dose = net_infusion_units(
                infusion_types[i],
                values[i],
                start_dates[i],
                end_dates[i],
                scheduled_basal_rates[i],
                delivered_units[i] if delivered_units else None,
            )
            if net_dose == 0:
                continue

            dose_start = start_dates[i] + timedelta(minutes=delay)
            time_since_start = time_interval_since(curr_date, dose_start) / 60.0  # in mins

            if time_since_start < 0:
                # Dose has not started yet
                continue
            elif time_since_start >= dia_mins:
                # Dose fully eliminated
                continue
            else:
                fraction_remaining = pk_model.fraction_active_remaining(time_since_start)
                hob_sum += net_dose * fraction_remaining

        hob_dates.append(curr_date)
        hob_values.append(max(0.0, hob_sum))
        curr_date += timedelta(minutes=delta)

    return (hob_dates, hob_values)


def cortisol_effects(
    infusion_types,
    start_dates,
    end_dates,
    values,
    scheduled_basal_rates,
    delivered_units,
    model_params,
    sensitivities_starts,
    sensitivities_ends,
    sensitivities_values,
    start=None,
    end=None,
    delay=10,
    delta=5,
):
    """Calculates blood cortisol concentration elevation effects (in ng/mL) resulting from hydrocortisone.

    Note: In contrast to insulin which lowers glucose (negative effect),
    hydrocortisone RAISES blood cortisol (positive effect).
    """
    if not infusion_types:
        return ([], [])

    pk_model = get_pk_model(model_params)
    dia_mins = pk_model.dia

    if start is None or end is None:
        start, end = simulation_date_range_for_samples(
            start_dates, end_dates, dia_mins, delay, delta
        )

    if start is None or end is None or start > end:
        return ([], [])

    effect_dates = []
    effect_values = []

    curr_date = start
    while curr_date <= end:
        total_effect = 0.0
        # Find sensitivity multiplier at this time
        sens = find_ratio_at_time(
            sensitivities_starts, sensitivities_ends, sensitivities_values, curr_date
        )

        for i in range(len(infusion_types)):
            net_dose = net_infusion_units(
                infusion_types[i],
                values[i],
                start_dates[i],
                end_dates[i],
                scheduled_basal_rates[i],
                delivered_units[i] if delivered_units else None,
            )
            if net_dose == 0:
                continue

            dose_start = start_dates[i] + timedelta(minutes=delay)
            time_since_start = time_interval_since(curr_date, dose_start) / 60.0

            if time_since_start < 0:
                fraction_absorbed = 0.0
            elif time_since_start >= dia_mins:
                fraction_absorbed = 1.0
            else:
                fraction_absorbed = 1.0 - pk_model.fraction_active_remaining(time_since_start)

            # Positive elevation in ng/mL: dose (mg) * sensitivity (ng/mL per mg) * fraction_absorbed
            total_effect += net_dose * sens * fraction_absorbed

        effect_dates.append(curr_date)
        effect_values.append(total_effect)
        curr_date += timedelta(minutes=delta)

    return (effect_dates, effect_values)


def find_ratio_at_time(ratio_start_times, ratio_end_times, ratio_values, query_datetime):
    """Finds the schedule value active at query_datetime."""
    if not ratio_values:
        return 30.0  # Default 30 ng/mL per mg HC

    q_time = query_datetime.time() if isinstance(query_datetime, datetime) else query_datetime

    for i in range(len(ratio_start_times)):
        start = ratio_start_times[i]
        end = ratio_end_times[i]
        if is_time_between(start, end, q_time):
            return ratio_values[i]

    return ratio_values[0]


def is_time_between(start, end, query_time):
    """Checks if query_time is in [start, end) supporting overnight wrap."""
    if start <= end:
        return start <= query_time <= end
    else:
        return query_time >= start or query_time <= end


def reconciled(infusion_types, start_dates, end_dates, values, delivered_units):
    """Reconciles overlapping infusions, trimming superseded temp basals and adjusting suspends."""
    if not infusion_types:
        return ([], [], [], [], [])

    # Sort entries by start time
    entries = sorted(
        zip(infusion_types, start_dates, end_dates, values, delivered_units if delivered_units else [None]*len(values)),
        key=lambda x: x[1]
    )

    out_types, out_starts, out_ends, out_values, out_delivered = [], [], [], [], []

    for t, s, e, v, d in entries:
        if t == InfusionType.tempbasal:
            # Trim previous temp basal if overlapping
            if out_types and out_types[-1] == InfusionType.tempbasal and out_ends[-1] > s:
                out_ends[-1] = s
        out_types.append(t)
        out_starts.append(s)
        out_ends.append(e)
        out_values.append(v)
        out_delivered.append(d)

    return (out_types, out_starts, out_ends, out_values, out_delivered)


def annotated(infusion_types, starts, ends, values, delivered_units, basal_starts, basal_rates, basal_minutes):
    """Annotates each infusion with the scheduled basal rate in effect."""
    annotated_basals = []
    for s in starts:
        # Determine active scheduled basal rate
        s_time = s.time()
        active_rate = basal_rates[0] if basal_rates else 0.5
        for b_start, b_rate, b_min in zip(basal_starts, basal_rates, basal_minutes):
            # Check schedule
            if s_time >= b_start:
                active_rate = b_rate
        annotated_basals.append(active_rate)
    return annotated_basals


# Aliases
hydrocortisone_on_board_calc = hydrocortisone_on_board
hob = hydrocortisone_on_board
glucose_effects = cortisol_effects
insulin_on_board = hydrocortisone_on_board
