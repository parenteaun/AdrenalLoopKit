#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circadian target curve modeling with linear interpolation between discrete time-series setpoints.
"""

from datetime import datetime, time, timedelta
from typing import List, Tuple, Union
import numpy as np


class CircadianCurveInterpolator:
    """Interpolates target cortisol values across a 24-hour cycle from discrete setpoints.

    Cortisol follows an asymmetric diurnal curve peaking sharply in early morning
    (4:00 AM - 8:00 AM) and nadiring around midnight. Linear interpolation between
    setpoints prevents step-change dosing artifacts.
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
