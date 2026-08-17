#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Date manipulation utilities for AdrenalLoopKit.
"""

from datetime import datetime, timedelta
import math


def time_interval_since(date_1, date_2):
    """ Return the difference between two datetime objects in seconds.
    Positive if date_1 is after date_2.
    """
    return (date_1 - date_2).total_seconds()


def date_floored_to_time_interval(date, interval_minutes):
    """ Round a datetime down to the nearest interval in minutes """
    if interval_minutes <= 0:
        return date
    interval_seconds = interval_minutes * 60
    timestamp = date.timestamp()
    floored_timestamp = math.floor(timestamp / interval_seconds) * interval_seconds
    return datetime.fromtimestamp(floored_timestamp, tz=date.tzinfo)


def date_ceiled_to_time_interval(date, interval_minutes):
    """ Round a datetime up to the nearest interval in minutes """
    if interval_minutes <= 0:
        return date
    interval_seconds = interval_minutes * 60
    timestamp = date.timestamp()
    ceiled_timestamp = math.ceil(timestamp / interval_seconds) * interval_seconds
    return datetime.fromtimestamp(ceiled_timestamp, tz=date.tzinfo)



def time_interval_since_reference_date(date):
    """ Return absolute difference between date and reference date (2001-01-01) in seconds """
    ref_date = datetime(2001, 1, 1, 0, 0, 0)
    return abs(time_interval_since(date, ref_date))

