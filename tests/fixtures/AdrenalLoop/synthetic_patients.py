#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic 24-hour Addison's disease patient scenarios and clinical fixtures.
"""

from datetime import datetime, time, timedelta
from adrenalloopkit.infusion import InfusionType


def generate_normal_24h_scenario(base_date=None):
    """Generates a standard 24-hour healthy circadian Addison's patient scenario."""
    if base_date is None:
        base_date = datetime(2026, 8, 17, 0, 0)

    # 24-hour timeline at 5-minute intervals (288 points)
    dates = [base_date + timedelta(minutes=5 * i) for i in range(288)]

    # Physiological cortisol curve (ng/mL):
    # Morning awakening surge peaking around 07:30 at ~175 ng/mL, nadir around midnight at ~35 ng/mL
    cortisol_values = []
    for d in dates:
        mins = d.hour * 60 + d.minute
        if mins < 240:  # 00:00 - 04:00: Nadir ~35-45 ng/mL
            val = 35.0 + 10.0 * (mins / 240.0)
        elif mins < 450:  # 04:00 - 07:30: Morning peak rising to 175 ng/mL
            val = 45.0 + 130.0 * ((mins - 240.0) / 210.0)
        elif mins < 720:  # 07:30 - 12:00: Post-morning descent to 110 ng/mL
            val = 175.0 - 65.0 * ((mins - 450.0) / 270.0)
        elif mins < 1080:  # 12:00 - 18:00: Afternoon descent to 75 ng/mL
            val = 110.0 - 35.0 * ((mins - 720.0) / 360.0)
        else:  # 18:00 - 24:00: Evening descent to 35 ng/mL
            val = 75.0 - 40.0 * ((mins - 1080.0) / 360.0)
        cortisol_values.append(round(val, 2))

    # Standard circadian target curve setpoints (10 setpoints across 24h)
    target_curve_starts = [
        time(0, 0), time(4, 0), time(6, 0), time(7, 30), time(9, 0),
        time(12, 0), time(15, 0), time(18, 0), time(21, 0), time(23, 59)
    ]
    target_curve_ends = target_curve_starts[1:] + [time(23, 59)]
    target_mins = [30.0, 40.0, 120.0, 160.0, 130.0, 90.0, 75.0, 60.0, 40.0, 30.0]
    target_maxes = [50.0, 60.0, 160.0, 200.0, 170.0, 130.0, 110.0, 90.0, 70.0, 50.0]

    # Scheduled basal profile (mg/hr)
    basal_starts = [time(0, 0), time(4, 0), time(8, 0), time(14, 0), time(20, 0)]
    basal_rates = [0.3, 1.2, 0.8, 0.6, 0.4]
    basal_minutes = [0, 240, 480, 840, 1200]

    scenario = {
        "cortisol_dates": dates,
        "cortisol_values": cortisol_values,
        "infusion_types": [InfusionType.basal],
        "infusion_start_times": [base_date],
        "infusion_end_times": [dates[-1]],
        "infusion_values": [0.6],
        "infusion_delivered_units": [14.4],
        "stress_dates": [],
        "stress_values": [],
        "stress_absorption_times": [],
        "settings_dictionary": {
            "model": [300, 80, 25],
            "momentum_data_interval": 15,
            "suspend_threshold": 30.0,
            "max_basal_rate": 2.0,
            "max_bolus": 5.0,
            "retrospective_correction_enabled": True,
        },
        "hydrocortisone_sensitivity_start_times": [time(0, 0)],
        "hydrocortisone_sensitivity_end_times": [time(23, 59)],
        "hydrocortisone_sensitivity_values": [30.0],
        "basal_rate_start_times": basal_starts,
        "basal_rate_values": basal_rates,
        "basal_rate_minutes": basal_minutes,
        "circadian_target_curve_start_times": target_curve_starts,
        "circadian_target_curve_end_times": target_curve_ends,
        "circadian_target_curve_minimum_values": target_mins,
        "circadian_target_curve_maximum_values": target_maxes,
        "time_to_calculate_at": base_date + timedelta(hours=12),
    }

    return scenario


def generate_acute_stress_scenario(base_date=None):
    """Generates a scenario where patient experiences an acute 45-min workout stress event."""
    scenario = generate_normal_24h_scenario(base_date)
    workout_time = scenario["cortisol_dates"][0] + timedelta(hours=14)  # 14:00

    # Add acute stress load
    scenario["stress_dates"] = [workout_time]
    scenario["stress_values"] = [60]
    scenario["stress_absorption_times"] = [90.0]  # 90 minutes decay
    scenario["time_to_calculate_at"] = workout_time + timedelta(minutes=30)

    return scenario


def generate_illness_infection_scenario(base_date=None):
    """Generates a prolonged fever/infection scenario requiring sustained basal escalation."""
    scenario = generate_normal_24h_scenario(base_date)
    illness_start = scenario["cortisol_dates"][0] + timedelta(hours=8)  # 08:00

    # Prolonged illness stress load
    scenario["stress_dates"] = [illness_start]
    scenario["stress_values"] = [100]
    scenario["stress_absorption_times"] = [720.0]  # 12 hours sustained demand
    scenario["time_to_calculate_at"] = illness_start + timedelta(hours=2)

    return scenario


def generate_near_crisis_scenario(base_date=None):
    """Generates an under-replacement scenario where cortisol drops to 24 ng/mL (crisis warning)."""
    scenario = generate_normal_24h_scenario(base_date)
    calc_time = scenario["cortisol_dates"][0] + timedelta(hours=10)

    # Artificially depress recent readings to crisis levels (<30 ng/mL)
    idx = [i for i, d in enumerate(scenario["cortisol_dates"]) if d <= calc_time]
    for i in idx[-6:]:
        scenario["cortisol_values"][i] = 22.0 + (i % 3)

    scenario["time_to_calculate_at"] = calc_time
    return scenario
