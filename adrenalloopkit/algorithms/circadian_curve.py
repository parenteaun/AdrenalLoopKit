#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circadian target curve modeling for Addison's disease management.

Provides:
- CircadianTargetGenerator: Dynamic 24-hour continuous mathematical target curve
  anchored to the patient's customizable wake time (exponential morning surge,
  gradual linear taper, flattening evening decay to sleep nadir).
- CircadianCurveInterpolator: Piecewise linear interpolation across discrete setpoints.
"""

from datetime import datetime, time, timedelta
import math
from typing import List, Tuple, Union


class CircadianTargetGenerator:
    """Generates continuous 24-hour physiological cortisol target curves
    dynamically anchored to the patient's wake time.

    Cortisol follows an asymmetric diurnal rhythm:
    - [Wake - 3h, Wake]: Aggressive exponential ramp (Cortisol Awakening Response / Morning Surge).
    - [Wake, Wake + 8h]: Gradual linear taper across active daytime hours.
    - [Wake + 8h, Wake + 17h]: Flattening quadratic/asymptotic taper to nocturnal sleep baseline.
    - [Wake + 17h, Wake - 3h]: Flat nocturnal sleep nadir baseline.
    """

    def __init__(
        self,
        wake_time: time = time(6, 0),
        baseline_target: float = 40.0,
        peak_target: float = 180.0,
        afternoon_target: float = 90.0,
        band_width: float = 40.0,
        surge_exponent: float = 2.5,
    ):
        """
        Arguments:
            wake_time -- datetime.time representing patient's habitual wake time (default 06:00)
            baseline_target -- Cortisol target at nocturnal sleep nadir in ng/mL (default 40.0)
            peak_target -- Cortisol target at awakening peak in ng/mL (default 180.0)
            afternoon_target -- Cortisol target at wake + 8h in ng/mL (default 90.0)
            band_width -- Width of acceptable target band (min = target - band/2, max = target + band/2)
            surge_exponent -- Exponential steepness factor k for morning surge ramp (default 2.5)
        """
        self.wake_time = wake_time
        self.wake_minutes = wake_time.hour * 60 + wake_time.minute + wake_time.second / 60.0
        self.baseline_target = float(baseline_target)
        self.peak_target = float(peak_target)
        self.afternoon_target = float(afternoon_target)
        self.band_width = float(band_width)
        self.half_band = self.band_width / 2.0
        self.surge_exponent = float(surge_exponent)

    def _relative_hours_from_wake(self, query_time: Union[time, datetime]) -> float:
        """Calculates hours relative to wake time mapped into [-3.0, 21.0)."""
        if isinstance(query_time, datetime):
            q_time = query_time.time()
        else:
            q_time = query_time

        q_mins = q_time.hour * 60.0 + q_time.minute + q_time.second / 60.0
        rel_hours = ((q_mins - self.wake_minutes) / 60.0) % 24.0
        if rel_hours >= 21.0:
            rel_hours -= 24.0  # Maps the 3-hour pre-wake window into [-3.0, 0.0)
        return rel_hours

    def target_value_at(self, query_time: Union[time, datetime]) -> float:
        """Evaluates the continuous physiological target cortisol value in ng/mL at query_time.

        Phases relative to wake time (T_wake):
        1. [T_wake - 3h, T_wake]: Aggressive exponential morning surge.
        2. [T_wake, T_wake + 8h]: Gradual linear taper.
        3. [T_wake + 8h, T_wake + 17h]: Flattening taper smoothly reaching baseline.
        4. [T_wake + 17h, T_wake - 3h]: Stable sleep baseline.
        """
        rel_hours = self._relative_hours_from_wake(query_time)

        # 1. [-3h, 0h]: Exponential Morning Surge (e.g. 3:00 AM - 6:00 AM)
        if -3.0 <= rel_hours < 0.0:
            u = (rel_hours + 3.0) / 3.0  # Normalized progress 0.0 -> 1.0
            k = self.surge_exponent
            exp_factor = (math.exp(k * u) - 1.0) / (math.exp(k) - 1.0)
            return self.baseline_target + (self.peak_target - self.baseline_target) * exp_factor

        # 2. [0h, 8h]: Gradual Linear Taper (e.g. 6:00 AM - 2:00 PM)
        elif 0.0 <= rel_hours < 8.0:
            u = rel_hours / 8.0  # 0.0 -> 1.0
            return self.peak_target - u * (self.peak_target - self.afternoon_target)

        # 3. [8h, 17h]: Flattening Taper to Baseline (e.g. 2:00 PM - 11:00 PM)
        elif 8.0 <= rel_hours < 17.0:
            u = (rel_hours - 8.0) / 9.0  # 0.0 -> 1.0
            decay_factor = (1.0 - u) ** 2  # Smooth quadratic flattening (d/du = 0 at u=1)
            return self.baseline_target + (self.afternoon_target - self.baseline_target) * decay_factor

        # 4. [17h, 21h]: Nocturnal Sleep Baseline (e.g. 11:00 PM - 3:00 AM)
        else:
            return self.baseline_target

    def target_at_time(self, query_time: Union[time, datetime]) -> Tuple[float, float]:
        """Calculates (min_target, max_target) cortisol values in ng/mL at query_time.

        Arguments:
            query_time -- datetime.time or datetime.datetime object

        Returns:
            (min_target_ng_per_ml, max_target_ng_per_ml)
        """
        center = self.target_value_at(query_time)
        min_target = max(0.0, center - self.half_band)
        max_target = center + self.half_band
        return (round(min_target, 2), round(max_target, 2))

    def target_series(
        self, start_time: datetime, end_time: datetime, interval_minutes: int = 5
    ) -> Tuple[List[datetime], List[float], List[float]]:
        """Generates time-series arrays of targets across a date range.

        Returns:
            (dates, min_targets, max_targets)
        """
        dates = []
        min_targets = []
        max_targets = []

        curr = start_time
        while curr <= end_time:
            min_v, max_v = self.target_at_time(curr)
            dates.append(curr)
            min_targets.append(min_v)
            max_targets.append(max_v)
            curr += timedelta(minutes=interval_minutes)

        return (dates, min_targets, max_targets)


def generate_circadian_target_curve(
    wake_time: time = time(6, 0),
    baseline_target: float = 40.0,
    peak_target: float = 180.0,
    afternoon_target: float = 90.0,
    band_width: float = 40.0,
) -> CircadianTargetGenerator:
    """Convenience factory function to create a 24-hour CircadianTargetGenerator."""
    return CircadianTargetGenerator(
        wake_time=wake_time,
        baseline_target=baseline_target,
        peak_target=peak_target,
        afternoon_target=afternoon_target,
        band_width=band_width,
    )


class CircadianCurveInterpolator:
    """Interpolates target cortisol values across a 24-hour cycle from discrete setpoints.

    Cortisol follows an asymmetric diurnal curve peaking sharply in early morning
    and nadiring around midnight. Linear interpolation between setpoints prevents
    step-change dosing artifacts when using discrete scheduling tables.
    """

    def __init__(
        self,
        setpoint_times: List[time],
        min_targets: List[float],
        max_targets: List[float],
    ):
        """
        Arguments:
            setpoint_times -- list of datetime.time objects for setpoints
            min_targets -- list of lower bound target cortisol values in ng/mL
            max_targets -- list of upper bound target cortisol values in ng/mL
        """
        assert len(setpoint_times) == len(min_targets) == len(max_targets), \
            "Setpoint times and target lists must have matching lengths"
        assert len(setpoint_times) >= 2, "Must provide at least 2 setpoints for interpolation"

        # Convert times to minutes from midnight (0 to 1440)
        self.minutes_and_targets = []
        for t, min_v, max_v in zip(setpoint_times, min_targets, max_targets):
            mins = t.hour * 60 + t.minute + t.second / 60.0
            self.minutes_and_targets.append((mins, float(min_v), float(max_v)))

        # Sort by minutes from midnight
        self.minutes_and_targets.sort(key=lambda x: x[0])

    @classmethod
    def create_standard_addison_curve(cls):
        """Creates a standard adult physiological circadian target curve:
        - 00:00 - 04:00: Nadir ~30-50 ng/mL
        - 04:00 - 07:00: Morning awakening surge rising to ~150-200 ng/mL
        - 08:00 - 12:00: Mid-morning drop to ~100-140 ng/mL
        - 12:00 - 18:00: Afternoon plateau ~70-100 ng/mL
        - 18:00 - 24:00: Evening descent to nadir ~40-60 ng/mL
        """
        setpoints = [
            (time(0, 0), 30.0, 50.0),
            (time(4, 0), 40.0, 60.0),
            (time(6, 0), 120.0, 160.0),
            (time(7, 30), 160.0, 200.0),
            (time(9, 0), 130.0, 170.0),
            (time(12, 0), 90.0, 130.0),
            (time(15, 0), 75.0, 110.0),
            (time(18, 0), 60.0, 90.0),
            (time(21, 0), 40.0, 70.0),
            (time(23, 59), 30.0, 50.0),
        ]
        times, mins, maxs = zip(*setpoints)
        return cls(list(times), list(mins), list(maxs))

    def target_at_time(self, query_time: Union[time, datetime]) -> Tuple[float, float]:
        """Linearly interpolates the (min_target, max_target) in ng/mL at the given time.

        Arguments:
            query_time -- datetime.time or datetime.datetime object

        Returns:
            (min_target_ng_per_ml, max_target_ng_per_ml)
        """
        if isinstance(query_time, datetime):
            q_time = query_time.time()
        else:
            q_time = query_time

        q_mins = q_time.hour * 60.0 + q_time.minute + q_time.second / 60.0

        # Exact match or find bounding setpoints
        pts = self.minutes_and_targets
        
        # If query is before first setpoint or after last setpoint, wrap around 24h
        if q_mins <= pts[0][0]:
            p0 = (pts[-1][0] - 1440.0, pts[-1][1], pts[-1][2])
            p1 = pts[0]
        elif q_mins >= pts[-1][0]:
            p0 = pts[-1]
            p1 = (pts[0][0] + 1440.0, pts[0][1], pts[0][2])
        else:
            p0 = pts[0]
            p1 = pts[1]
            for i in range(len(pts) - 1):
                if pts[i][0] <= q_mins <= pts[i + 1][0]:
                    p0 = pts[i]
                    p1 = pts[i + 1]
                    break

        span = p1[0] - p0[0]
        if span == 0:
            return (p0[1], p0[2])

        fraction = (q_mins - p0[0]) / span
        min_val = p0[1] + fraction * (p1[1] - p0[1])
        max_val = p0[2] + fraction * (p1[2] - p0[2])

        return (min_val, max_val)

    def target_series(
        self, start_time: datetime, end_time: datetime, interval_minutes: int = 5
    ) -> Tuple[List[datetime], List[float], List[float]]:
        """Generates time-series arrays of linearly interpolated targets.

        Returns:
            (dates, min_targets, max_targets)
        """
        dates = []
        min_targets = []
        max_targets = []

        curr = start_time
        while curr <= end_time:
            min_v, max_v = self.target_at_time(curr)
            dates.append(curr)
            min_targets.append(min_v)
            max_targets.append(max_v)
            curr += timedelta(minutes=interval_minutes)

        return (dates, min_targets, max_targets)
