#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdrenalLoopKit data serialization and report parsing utilities.
"""

import json
from datetime import datetime, time, timedelta

from adrenalloopkit.models.domain_models import InfusionType
from adrenalloopkit.manager.adrenal_data_manager import update


def parse_adrenal_report_and_run(file_path):
    """Loads an AdrenalLoop JSON issue report and runs the update algorithm."""
    with open(file_path, "r") as f:
        data = json.load(f)

    # Parse ISO dates
    for key in ["cortisol_dates", "glucose_dates", "infusion_start_times", "infusion_end_times", "stress_dates"]:
        if key in data and data[key]:
            data[key] = [datetime.fromisoformat(d) if isinstance(d, str) else d for d in data[key]]

    for key in ["circadian_target_curve_start_times", "circadian_target_curve_end_times", "hydrocortisone_sensitivity_start_times", "hydrocortisone_sensitivity_end_times"]:
        if key in data and data[key]:
            data[key] = [time.fromisoformat(t) if isinstance(t, str) else t for t in data[key]]

    if "infusion_types" in data and data["infusion_types"]:
        data["infusion_types"] = [InfusionType.from_str(t) if isinstance(t, str) else t for t in data["infusion_types"]]

    if "time_to_calculate_at" in data and isinstance(data["time_to_calculate_at"], str):
        data["time_to_calculate_at"] = datetime.fromisoformat(data["time_to_calculate_at"])

    return update(data)


# Aliases
parse_report_and_run = parse_adrenal_report_and_run
