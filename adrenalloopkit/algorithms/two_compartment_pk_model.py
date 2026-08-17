#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Two-compartment and exponential Pharmacokinetic (PK) models for subcutaneous hydrocortisone.

Subcutaneous hydrocortisone infusion kinetics:
- Compartment 1: Subcutaneous depot absorption with rate constant ka (t_half_ka ~ 20-30 mins)
- Compartment 2: Central vascular plasma compartment with elimination rate constant ke (t_half_ke ~ 70-90 mins)
"""

import math
from typing import Tuple


class HydrocortisoneTwoCompartmentModel:
    """2-Compartment Pharmacokinetic model for subcutaneous hydrocortisone infusion.

    Parameters:
        absorption_half_life (float): Subcutaneous absorption half-life in minutes (default: 25 mins).
        elimination_half_life (float): Plasma elimination half-life in minutes (default: 80 mins).
        duration_of_action (float): Effective duration in minutes (default: 300 mins / 5 hours).
    """

    def __init__(
        self,
        absorption_half_life: float = 25.0,
        elimination_half_life: float = 80.0,
        duration_of_action: float = 300.0,
    ):
        self.ka = math.log(2) / absorption_half_life  # absorption rate constant (min^-1)
        self.ke = math.log(2) / elimination_half_life  # elimination rate constant (min^-1)
        self.dia = duration_of_action

        # Normalization factor for unit area under curve
        if self.ka == self.ke:
            self.ka += 0.0001
        self.scale = self.ka / (self.ka - self.ke)

    def fraction_active_remaining(self, time_minutes: float) -> float:
        """Returns the fraction of hydrocortisone dose remaining active / uneliminated at time t.
        Decays from 1.0 at t=0 to 0.0 at t >= DIA.
        """
        if time_minutes <= 0:
            return 1.0
        if time_minutes >= self.dia:
            return 0.0

        t = time_minutes
        # Integrated fraction remaining in system (subQ + plasma)
        # SubQ remaining: e^(-ka * t)
        # Plasma remaining: scale * [ (ka/ke)*(1 - e^(-ke*t)) - (1 - e^(-ka*t)) ] ...
        # Simplified standard 2-compartment total body fraction remaining:
        frac = (self.ka * math.exp(-self.ke * t) - self.ke * math.exp(-self.ka * t)) / (self.ka - self.ke)
        frac = max(0.0, min(1.0, frac))

        # Adjust for finite DIA cutoff
        dia_frac = (self.ka * math.exp(-self.ke * self.dia) - self.ke * math.exp(-self.ka * self.dia)) / (self.ka - self.ke)
        adjusted = (frac - dia_frac) / (1.0 - dia_frac)
        return max(0.0, min(1.0, adjusted))

    def plasma_activity_rate(self, time_minutes: float) -> float:
        """Returns the instantaneous rate of plasma concentration / activity at time t (normalized).
        Peaks around 45-65 minutes post-dose.
        """
        if time_minutes <= 0 or time_minutes >= self.dia:
            return 0.0

        t = time_minutes
        activity = self.scale * (math.exp(-self.ke * t) - math.exp(-self.ka * t))
        return max(0.0, activity)


class HydrocortisoneExponentialModel:
    """1-Compartment exponential model for hydrocortisone (duration and peak parameterization)."""

    def __init__(self, duration_minutes: float = 300.0, peak_minutes: float = 65.0):
        self.dia = duration_minutes
        self.peak = peak_minutes
        self.tau = peak_minutes * (1 - peak_minutes / duration_minutes) / (1 - 2 * peak_minutes / duration_minutes)
        self.a = 2 * self.tau / duration_minutes
        self.s = 1 / (1 - self.a + (1 + self.a) * math.exp(-duration_minutes / self.tau))

    def fraction_active_remaining(self, time_minutes: float) -> float:
        if time_minutes <= 0:
            return 1.0
        if time_minutes >= self.dia:
            return 0.0

        t = time_minutes
        frac = 1 - self.s * (1 - self.a) * ((t**2 / (2 * self.tau * self.dia)) - t / self.dia - 1) - self.s * math.exp(-t / self.tau)
        return max(0.0, min(1.0, frac))

    def plasma_activity_rate(self, time_minutes: float) -> float:
        if time_minutes <= 0 or time_minutes >= self.dia:
            return 0.0
        t = time_minutes
        activity = (self.s / self.tau) * (1 - t / self.dia) * (1 - math.exp(-t / self.tau))
        return max(0.0, activity)
