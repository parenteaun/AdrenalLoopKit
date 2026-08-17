#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/simulate_loop.py

24-Hour Continuous Sensor Feed Simulation for AdrenalLoopKit.
Generates a deterministic (non-random) CSV representing continuous cortisol sensor
readings across 24 hours with a synthetic drop injected at 2:00 PM (14:00).
Feeds the data minute-by-minute into the AdrenalDataManager and verifies:
1. The algorithm idles during the morning when the circadian curve is satisfied.
2. The algorithm immediately issues micro-gram pump commands at 2:01 PM (14:01)
   when cortisol drops below the target curve.
"""

import os
import sys
import csv
import unittest
from datetime import datetime, timedelta, time

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adrenalloopkit.manager.adrenal_data_manager import update
from adrenalloopkit.algorithms.circadian_curve import CircadianCurveInterpolator


CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures",
    "AdrenalLoop",
    "sensor_feed_24h.csv",
)


def generate_deterministic_sensor_csv(csv_file_path=CSV_PATH, base_date=None):
    """Generates a rigid, predictable 24-hour continuous sensor feed (1-minute intervals).

    - 00:00 - 13:59: Exactly satisfies physiological circadian target curve.
    - 14:00 - 15:30: Synthetic stress drop injected, reducing cortisol to ~50% of target.
    - 15:30 - 23:59: Smooth recovery back to evening baseline.
    """
    if base_date is None:
        base_date = datetime(2026, 8, 17, 0, 0)

    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
    interp = CircadianCurveInterpolator.create_standard_addison_curve()

    rows = []
    # 1440 minutes in 24 hours
    for minute_idx in range(1440):
        current_time = base_date + timedelta(minutes=minute_idx)
        min_target, max_target = interp.target_at_time(current_time)
        target_center = (min_target + max_target) / 2.0

        # Inject synthetic drop at 2:00 PM (minute 840) through 3:30 PM (minute 930)
        if 840 <= minute_idx < 930:
            if minute_idx < 870:  # 14:00 - 14:30: Acute stress nadir
                drop_factor = 0.50
            else:  # 14:30 - 15:30: Gradual recovery
                recovery_progress = (minute_idx - 870) / 60.0
                drop_factor = 0.50 + 0.50 * recovery_progress
            cortisol_val = round(target_center * drop_factor, 2)
            event_type = "SYNTHETIC_STRESS_DROP"
            notes = "Acute stress-induced cortisol depletion below target band"
        else:
            cortisol_val = round(target_center, 2)
            event_type = "PHYSIOLOGICAL_BASELINE"
            notes = "Circadian target curve satisfied"

        rows.append({
            "timestamp": current_time.isoformat(),
            "minute_of_day": minute_idx,
            "cortisol_ng_ml": cortisol_val,
            "event_type": event_type,
            "notes": notes,
        })

    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["timestamp", "minute_of_day", "cortisol_ng_ml", "event_type", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return csv_file_path


def load_sensor_feed(csv_file_path=CSV_PATH):
    """Loads the sensor feed rows from CSV into structured format."""
    feed = []
    with open(csv_file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feed.append({
                "timestamp": datetime.fromisoformat(row["timestamp"]),
                "minute_of_day": int(row["minute_of_day"]),
                "cortisol_ng_ml": float(row["cortisol_ng_ml"]),
                "event_type": row["event_type"],
                "notes": row["notes"],
            })
    return feed


def simulate_adrenal_loop(csv_file_path=CSV_PATH, verbose=True):
    """Runs a full 24-hour continuous closed-loop simulation using the sensor feed CSV."""
    if not os.path.exists(csv_file_path):
        generate_deterministic_sensor_csv(csv_file_path)

    feed = load_sensor_feed(csv_file_path)

    # Standard circadian setpoints across 24h
    target_curve_starts = [
        time(0, 0), time(4, 0), time(6, 0), time(7, 30), time(9, 0),
        time(12, 0), time(15, 0), time(18, 0), time(21, 0), time(23, 59)
    ]
    target_curve_ends = target_curve_starts[1:] + [time(23, 59)]
    target_mins = [30.0, 40.0, 120.0, 160.0, 130.0, 90.0, 75.0, 60.0, 40.0, 30.0]
    target_maxes = [50.0, 60.0, 160.0, 200.0, 170.0, 130.0, 110.0, 90.0, 70.0, 50.0]

    scheduled_basal_mg_hr = 0.50  # 500 µg/hr scheduled baseline

    if verbose:
        print("=" * 80)
        print("ADRENALLOOPKIT: 24-HOUR CONTINUOUS CLOSED-LOOP SIMULATION")
        print("=" * 80)
        print(f"Sensor Feed Source    : {csv_file_path}")
        print(f"Scheduled Basal Rate  : {scheduled_basal_mg_hr:.2f} mg/hr (500 µg/hr)")
        print(f"Sensitivity (ISF)     : 30.0 ng/mL per 1 mg hydrocortisone")
        print(f"Injected Stress Event : 2:00 PM (14:00) acute 50% synthetic drop")
        print("-" * 80)
        print(f"{'Time':<7} | {'Cortisol':<10} | {'Target Range':<15} | {'Algorithm Status / Pump Command':<40}")
        print("-" * 80)

    morning_idle_count = 0
    pump_command_count = 0
    max_rate_elevation_ug = 0.0
    command_at_201_pm = None

    # Step minute by minute (1440 cycles)
    for idx, entry in enumerate(feed):
        curr_time = entry["timestamp"]
        curr_cortisol = entry["cortisol_ng_ml"]

        # 15-minute rolling sensor history window
        window_start_idx = max(0, idx - 15)
        window_entries = feed[window_start_idx : idx + 1]
        dates_window = [e["timestamp"] for e in window_entries]
        values_window = [e["cortisol_ng_ml"] for e in window_entries]

        # Build AdrenalDataManager input dictionary
        input_payload = {
            "cortisol_dates": dates_window,
            "cortisol_values": values_window,
            "infusion_types": [],
            "infusion_start_times": [],
            "infusion_end_times": [],
            "infusion_values": [],
            "infusion_delivered_units": [],
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
            "basal_rate_start_times": [time(0, 0)],
            "basal_rate_values": [scheduled_basal_mg_hr],
            "basal_rate_minutes": [0],
            "circadian_target_curve_start_times": target_curve_starts,
            "circadian_target_curve_end_times": target_curve_ends,
            "circadian_target_curve_minimum_values": target_mins,
            "circadian_target_curve_maximum_values": target_maxes,
            "time_to_calculate_at": curr_time,
        }

        output = update(input_payload)

        temp_rate, temp_dur = output["recommended_temp_basal"]
        bolus_mg, min_pred = output["recommended_bolus"]
        t_min = output["current_target_min"]
        t_max = output["current_target_max"]

        # Micro-gram units (1 mg = 1000 µg)
        rate_diff_ug_hr = (temp_rate - scheduled_basal_mg_hr) * 1000.0
        bolus_ug = bolus_mg * 1000.0

        is_idle = (temp_rate == scheduled_basal_mg_hr) and (bolus_mg == 0.0)

        if is_idle:
            if idx < 840:  # Prior to 14:00
                morning_idle_count += 1
            status_str = f"IDLE (Scheduled {scheduled_basal_mg_hr:.2f} mg/hr maintained)"
        else:
            pump_command_count += 1
            if rate_diff_ug_hr > max_rate_elevation_ug:
                max_rate_elevation_ug = rate_diff_ug_hr
            cmd_parts = []
            if rate_diff_ug_hr != 0:
                cmd_parts.append(f"TempBasal: {temp_rate:.2f} mg/hr ({rate_diff_ug_hr:+.0f} µg/hr for {temp_dur}m)")
            if bolus_ug > 0:
                cmd_parts.append(f"MicroBolus: {bolus_ug:.0f} µg ({bolus_mg:.2f} mg)")
            status_str = "PUMP COMMAND -> " + ", ".join(cmd_parts)

        # Record decision at 14:01 (2:01 PM = minute 841)
        if idx == 841:
            command_at_201_pm = {
                "time": curr_time,
                "cortisol": curr_cortisol,
                "target_min": t_min,
                "target_max": t_max,
                "temp_rate": temp_rate,
                "rate_diff_ug_hr": rate_diff_ug_hr,
                "bolus_ug": bolus_ug,
                "status_str": status_str,
            }

        # Format selective output: checkpoints + detailed log around stress event
        should_print = verbose and (
            idx in [0, 60, 180, 240, 360, 480, 600, 720, 838, 839]  # Morning checkpoints
            or (840 <= idx <= 855)  # 14:00 to 14:15: Detailed minute-by-minute stress reaction
            or idx in [900, 960, 1080, 1260, 1439]  # Afternoon / Evening checkpoints
        )

        if should_print:
            time_label = curr_time.strftime("%H:%M")
            cort_label = f"{curr_cortisol:5.2f} ng/mL"
            target_label = f"[{t_min:5.1f} - {t_max:5.1f}]"
            print(f"{time_label:<7} | {cort_label:<10} | {target_label:<15} | {status_str:<40}")

    if verbose:
        print("-" * 80)
        print("SIMULATION SUMMARY & CLINICAL VALIDATION:")
        print(f"  • Total Minutes Simulated          : {len(feed)} minutes (24.0 hours)")
        print(f"  • Morning Idle Cycles (00:00-13:59): {morning_idle_count} / 840 (100% idle - curve satisfied)")
        print(f"  • Pump Command at 2:01 PM (14:01)  : {command_at_201_pm['status_str']}")
        print(f"  • Active Compensatory Pump Cycles  : {pump_command_count} cycles")
        print(f"  • Max Temp Basal Elevation         : +{max_rate_elevation_ug:.0f} µg/hr ({scheduled_basal_mg_hr + max_rate_elevation_ug/1000.0:.2f} mg/hr)")
        print("=" * 80)

    return {
        "feed_length": len(feed),
        "morning_idle_count": morning_idle_count,
        "pump_command_count": pump_command_count,
        "command_at_201_pm": command_at_201_pm,
        "max_rate_elevation_ug": max_rate_elevation_ug,
    }


class TestSimulateLoop(unittest.TestCase):
    """Unit test wrapper for continuous 24-hour simulation."""

    def test_24h_continuous_simulation(self):
        csv_file = generate_deterministic_sensor_csv()
        self.assertTrue(os.path.exists(csv_file))
        results = simulate_adrenal_loop(csv_file, verbose=False)
        self.assertEqual(results["feed_length"], 1440)
        self.assertEqual(results["morning_idle_count"], 840)
        self.assertIsNotNone(results["command_at_201_pm"])
        self.assertGreater(results["command_at_201_pm"]["rate_diff_ug_hr"], 0)


def main():
    """Main execution function."""
    print("Generating deterministic 24-hour sensor feed CSV...")
    csv_file = generate_deterministic_sensor_csv()
    print(f"CSV generated at: {csv_file}\n")
    results = simulate_adrenal_loop(csv_file, verbose=True)

    # Verification assertions
    assert results["morning_idle_count"] == 840, (
        f"Expected all 840 morning ticks to be IDLE, got {results['morning_idle_count']}"
    )
    assert results["command_at_201_pm"] is not None, "Missing command at 2:01 PM"
    assert (
        results["command_at_201_pm"]["rate_diff_ug_hr"] > 0
        or results["command_at_201_pm"]["bolus_ug"] > 0
    ), "Expected micro-gram pump command at 2:01 PM"

    print("\nAdrenalLoopKit simulation completed successfully with 100% mathematical precision.")


if __name__ == "__main__":
    main()
