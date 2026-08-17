# AdrenalLoopKit Living Uncertainty & Architectural Decision Registry

This document serves as the standardized, persistent store of known unknowns, physiological model uncertainties, algorithmic approximations, and clinical review items for **AdrenalLoopKit**.

---

## 1. Registry Index

| ID | Title | Domain Area | Risk Level | Status |
| :--- | :--- | :--- | :--- | :--- |
| `[UNC-01]` | Pharmacokinetic (PK) Model MVP vs. 2-Compartment | PK / Drug Kinetics | Medium | Open |
| `[UNC-02]` | Stress Decay & Recovery Math Formulation | Disturbance Modeling | High | Open |
| `[UNC-03]` | Absolute Software Bounds for Automated Delivery | Clinical Safety | High | Open |

---

## 2. Detailed Uncertainty Entries

### [UNC-01] Pharmacokinetic (PK) Model MVP vs. 2-Compartment Model
* **Status**: `Open`
* **Domain Area**: `adrenalloopkit.pharmacokinetics` / `adrenalloopkit.dose`
* **Current State / Approximation**:
  - Implemented 2-compartment pharmacokinetic model accounting for absorption delay from subcutaneous depot into blood plasma, followed by metabolic clearance.
* **Clinical & Engineering Uncertainty**:
  - Whether a simpler 1-compartment exponential model with a fixed time-to-peak is adequate for the Minimum Viable Product (MVP), or if the full 2-compartment model is strictly necessary across all patient age and BMI strata to prevent dose stacking.
* **Resolution Criteria / Validation Needed**:
  - Clinical microdialysis / subcutaneous pump PK studies comparing observed plasma cortisol curves against 1-compartment vs. 2-compartment simulations.

---

### [UNC-02] Biometric Stress Quantization & Decay Kinetics
* **Status**: `Open`
* **Domain Area**: `adrenalloopkit.stress` / `adrenalloopkit.wearables`
* **Current State / Approximation**:
  - Modeled dynamic stress demands categorized by classification (acute physical/emotional stress vs. systemic illness/infection).
* **Clinical & Engineering Uncertainty**:
  - Unlike carbohydrates (which have well-defined glycemic indexes and absorption curves), quantifying biometric stress metrics (HRV drop, EDA spikes, core temperature) into cortisol clearance equivalents is theoretical in current clinical literature.
* **Resolution Criteria / Validation Needed**:
  - Prospective observational trials correlating biometric wearable metrics with continuous cortisol biosensor declines during controlled physical and psychological stress challenges.

---

### [UNC-03] Absolute Software Bounds & Override Logic for Automated Infusion
* **Status**: `Open`
* **Domain Area**: `adrenalloopkit.safety` / `adrenalloopkit.pump`
* **Current State / Approximation**:
  - Sensor bounds: Normal $20–250\text{ ng/mL}$; Crisis alert $<30\text{ ng/mL}$; Over-replacement alert $>350\text{ ng/mL}$.
  - Infusion caps: Daily replacement $15–25\text{ mg/day}$; Max basal cap $2.0\text{ mg/hr}$; Max stress bolus cap $5.0–10.0\text{ mg}$.
* **Clinical & Engineering Uncertainty**:
  - Subcutaneous hydrocortisone closed-loop control is experimental. Hard-coded bounds must balance preventing adrenal crisis (under-replacement) against preventing steroid psychosis / hypertensive crisis (over-replacement).
* **Resolution Criteria / Validation Needed**:
  - Clinical protocol consensus on strict customizable per-patient safety envelopes with mandatory physician override authorization.
