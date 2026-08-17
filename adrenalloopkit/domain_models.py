#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdrenalLoopKit domain models and data structures for Addison's Disease management.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, List, Union
from enum import Enum


class InfusionType(Enum):
    """Types of hydrocortisone infusions."""
    basal = "basal"
    bolus = "bolus"
    tempbasal = "tempbasal"
    suspend = "suspend"
    resume = "resume"
    stress_bolus = "stress_bolus"

    @classmethod
    def from_str(cls, label: str):
        if not label:
            return cls.basal
        l = label.lower()
        if "bolus" in l or "meal" in l:
            return cls.bolus
        elif "temp" in l:
            return cls.tempbasal
        elif "suspend" in l:
            return cls.suspend
        elif "resume" in l:
            return cls.resume
        elif "stress" in l:
            return cls.stress_bolus
        return cls.basal


# Legacy DoseType alias
DoseType = InfusionType


@dataclass
class CortisolValue:
    """Continuous wearable sensor cortisol measurement.

    Attributes:
        date (datetime): Timestamp of measurement.
        value (float): Cortisol concentration in blood/interstitial fluid (ng/mL).
        provenance (Optional[str]): Source/device provenance identifier.
    """
    date: datetime
    value: float
    provenance: Optional[str] = None

    def __post_init__(self):
        self.value = float(self.value)


@dataclass
class StressLoad:
    """Biometric stress load metric representing physiological/psychological stress events.

    Attributes:
        date (datetime): Time when stress load began/occurred.
        value (int): Calculated integer stress load index from biometric wearables.
        absorption_time (Optional[float]): Estimated duration/decay of stress impact (minutes).
        stress_type (str): 'acute' (fast decay) or 'illness' (prolonged sustained demand).
    """
    date: datetime
    value: int
    absorption_time: Optional[float] = 180.0
    stress_type: str = "acute"

    def __post_init__(self):
        self.value = int(self.value)
        if self.absorption_time is not None:
            self.absorption_time = float(self.absorption_time)


@dataclass
class InfusionEntry:
    """Hydrocortisone infusion entry (basal rate or bolus).

    Attributes:
        type (InfusionType): Infusion type (basal, tempbasal, bolus, suspend, resume, stress_bolus).
        start_time (datetime): Start timestamp of delivery.
        end_time (datetime): End timestamp of delivery.
        value (float): Rate in mg/hr (for basal) or total dose in mg (for bolus).
        delivered_units (Optional[float]): Actual milligrams delivered if known.
    """
    type: InfusionType
    start_time: datetime
    end_time: datetime
    value: float
    delivered_units: Optional[float] = None

    def __post_init__(self):
        self.value = float(self.value)
        if self.delivered_units is not None:
            self.delivered_units = float(self.delivered_units)


@dataclass
class HydrocortisoneOnBoard:
    """Active hydrocortisone on board (HOB) tracking the decay timeline.

    Attributes:
        date (datetime): Timestamp of calculation.
        value (float): Milligrams of active hydrocortisone remaining.
    """
    date: datetime
    value: float

    def __post_init__(self):
        self.value = float(self.value)


# Short alias for HydrocortisoneOnBoard
HOB = HydrocortisoneOnBoard


@dataclass
class CircadianTargetCurve:
    """24-hour variable target curve representing physiological circadian cortisol targets.

    Attributes:
        start_time (time): Start time of schedule interval.
        end_time (time): End time of schedule interval.
        min_cortisol (float): Lower bound target cortisol in ng/mL.
        max_cortisol (float): Upper bound target cortisol in ng/mL.
    """
    start_time: time
    end_time: time
    min_cortisol: float
    max_cortisol: float

    def __post_init__(self):
        self.min_cortisol = float(self.min_cortisol)
        self.max_cortisol = float(self.max_cortisol)


@dataclass
class HydrocortisoneSensitivity:
    """Hydrocortisone sensitivity multiplier schedule (effect of HC on blood cortisol).

    Attributes:
        start_time (time): Start time of sensitivity schedule.
        end_time (time): End time of sensitivity schedule.
        value (float): Sensitivity multiplier in ng/mL rise per 1 mg hydrocortisone.
    """
    start_time: time
    end_time: time
    value: float

    def __post_init__(self):
        self.value = float(self.value)


# Legacy Aliases
GlucoseValue = CortisolValue
CarbEntry = StressLoad
DoseEntry = InfusionEntry
InsulinOnBoard = HydrocortisoneOnBoard
IOB = HOB
TargetRange = CircadianTargetCurve
InsulinSensitivityFactor = HydrocortisoneSensitivity
