#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdrenalLoopKit Demonstration: Running the Addison's Disease Closed-Loop Controller
with a 24-hour synthetic patient scenario.
"""

from datetime import datetime, timedelta
from adrenalloopkit import update
from tests.fixtures.AdrenalLoop.synthetic_patients import (
    generate_normal_24h_scenario,
    generate_acute_stress_scenario,
    generate_illness_infection_scenario,
)


def run_demo():
    print("=" * 70)
    print("AdrenalLoopKit: Automated Hormone Delivery for Addison's Disease")
    print("=" * 70)

    # 1. Run Standard 24h Patient Scenario
    normal_scenario = generate_normal_24h_scenario()
    output_normal = update(normal_scenario)

    print("\n--- 1. Normal Circadian Scenario ---")
    print(f"Target Range at query time: {output_normal['current_target_min']:.1f} - {output_normal['current_target_max']:.1f} ng/mL")
    print(f"Active Hydrocortisone On Board (HOB): {output_normal['hydrocortisone_on_board']:.2f} mg")
    rate, dur = output_normal["recommended_temp_basal"]
    print(f"Recommended Temp Basal: {rate:.2f} mg/hr for {dur} mins")

    # 2. Run Acute Workout Stress Scenario
    stress_scenario = generate_acute_stress_scenario()
    output_stress = update(stress_scenario)

    print("\n--- 2. Acute Workout Stress Scenario ---")
    print(f"Active Stress Load on Board: {output_stress['stress_load_on_board']:.1f}")
    rate_s, dur_s = output_stress["recommended_temp_basal"]
    bolus_s, min_pred_s = output_stress["recommended_bolus"]
    print(f"Recommended Temp Basal: {rate_s:.2f} mg/hr for {dur_s} mins")
    print(f"Recommended Stress Bolus: {bolus_s:.2f} mg")

    # 3. Run Prolonged Illness / Infection Scenario
    illness_scenario = generate_illness_infection_scenario()
    output_illness = update(illness_scenario)

    print("\n--- 3. Prolonged Illness / Infection Scenario ---")
    print(f"Active Illness Stress Load on Board: {output_illness['stress_load_on_board']:.1f}")
    rate_i, dur_i = output_illness["recommended_temp_basal"]
    print(f"Compensatory Elevated Temp Basal: {rate_i:.2f} mg/hr for {dur_i} mins")
    print("\nAdrenalLoopKit execution completed successfully.")


if __name__ == "__main__":
    run_demo()
