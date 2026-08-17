#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrocortisone infusion history storage and effect caching for AdrenalLoopKit.
"""

from adrenalloopkit.algorithms.hydrocortisone_math import (
    hydrocortisone_on_board,
    cortisol_effects,
    reconciled,
    annotated,
)


def get_cortisol_effects(
    infusion_types,
    start_dates,
    end_dates,
    values,
    scheduled_basal_rates,
    delivered_units,
    model_params,
    sens_starts,
    sens_ends,
    sens_values,
    start=None,
    end=None,
    delay=10,
    delta=5,
):
    """Calculates cortisol elevation effect timeline from hydrocortisone doses."""
    return cortisol_effects(
        infusion_types,
        start_dates,
        end_dates,
        values,
        scheduled_basal_rates,
        delivered_units,
        model_params,
        sens_starts,
        sens_ends,
        sens_values,
        start=start,
        end=end,
        delay=delay,
        delta=delta,
    )

