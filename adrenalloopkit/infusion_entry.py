#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrocortisone infusion entry math and net delivery calculations in milligrams (mg).
"""
from adrenalloopkit.date import time_interval_since
from adrenalloopkit.infusion import InfusionType, DoseType
from adrenalloopkit.domain_models import InfusionEntry, DoseEntry


def net_infusion_units(type_, value, start, end, scheduled_basal_rate, delivered_units):
    """ Find the milligrams of hydrocortisone delivered, net of any scheduled basal rate
        (if infusion is a temp basal)

    Arguments:
    type_ -- type of infusion (basal, bolus, tempbasal, suspend, etc)
    value -- if bolus: amount given (mg), if temp basal: temp rate (mg/hr)
    start -- datetime object representing start of infusion
    end -- datetime object representing end of infusion
    scheduled_basal_rate -- the rate scheduled during the time the infusion was
                            given (0 for boluses)
    delivered_units -- units/mg actually delivered by pump

    Output:
    Bolus amount (if a bolus), or basal mg given, net of whatever the
    scheduled basal is
    """
    MINIMUM_PUMP_INCREMENT = 20

    if type_ in [InfusionType.bolus, InfusionType.stress_bolus]:
        return delivered_units if delivered_units is not None else value

    elif type_ == InfusionType.basal:
        return 0

    hours_ = hours(end, start)

    if hours_ <= 0:
        return 0

    if type_ == InfusionType.suspend:
        scheduled_units = -scheduled_basal_rate * hours_
    else:
        scheduled_units = (value - scheduled_basal_rate) * hours_

    net_delivered_units = None
    if delivered_units is not None:
        net_delivered_units = delivered_units - (scheduled_basal_rate * hours_)

    return net_delivered_units if net_delivered_units is not None else round(scheduled_units * MINIMUM_PUMP_INCREMENT) / MINIMUM_PUMP_INCREMENT


def total_units_given(type_, value, start, end):
    """ Find total mg of hydrocortisone given for an infusion """
    if type_ in [InfusionType.bolus, InfusionType.stress_bolus, InfusionType.suspend]:
        return value

    return value * hours(end, start)


def hours(start_date, end_date):
    """ Find hours between two dates for basal delivery """
    return abs(time_interval_since(end_date, start_date)) / 3600.0


# Legacy and domain aliases
net_basal_units = net_infusion_units
total_infusion_units = total_units_given
