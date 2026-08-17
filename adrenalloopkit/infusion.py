#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrocortisone infusion types and classifications for AdrenalLoopKit.
"""
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
