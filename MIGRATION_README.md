# AdrenalLoopKit Migration & Architectural Readiness Log

This document serves as a living log of architectural decisions, physiological models, clinical safety considerations, and known unknowns for the development and clinical team.

---

## 1. Domain Overview & Scope Transition

AdrenalLoopKit is a closed-loop automated hormone delivery algorithm designed specifically for the management of **Primary and Secondary Adrenal Insufficiency (Addison's Disease)**, refactored from the PyLoopKit model-predictive controller architecture.

### Conceptual Mapping

| Diabetes Concept | Addison's Disease Concept | Biological Mechanism in AdrenalLoop |
| :--- | :--- | :--- |
| **Glucose** ($\text{mg/dL}$) | **Cortisol** ($\text{ng/mL}$) | Target controlled variable measured via continuous wearable sensor ($10\text{ ng/mL} = 1\ \mu\text{g/dL}$). |
| **Insulin** ($\text{U}$) | **Hydrocortisone** ($\text{mg}$) | Hormone replacement delivered continuously via subcutaneous infusion pump ($1\text{ mg} = 1000\ \mu\text{g}$). |
| **Hormone Effect** (Negative) | **Hormone Effect** (Positive) | Hydrocortisone **elevates** blood cortisol concentration ($Cortisol(t) = Baseline + \sum Infusion \times Sens \times Decay(t)$). |
| **Carbohydrates** ($\text{g}$) | **Stress Load** (Index) | Active disturbance causing increased physiological demand / rapid cortisol depletion. |
| **Carb Absorption** | **Stress Demand / Recovery** | Acute stress (rapid spike, exponential recovery) vs. illness/infection (sustained prolonged demand). |
| **Flat Target Range** | **Circadian Target Curve** | Asymmetric 24-hour diurnal rhythm (early morning awakening spike 4:00–8:00 AM, gradual decline to midnight nadir). |
| **IOB** (Insulin on Board) | **HOB** (Hydrocortisone on Board) | Active circulating / remaining hydrocortisone tracking across the 2-compartment decay timeline. |

---

## 2. Living Log of Architectural Uncertainties & Clinical Reviews

The following items represent areas where algorithmic confidence is currently iterative and will require ongoing clinical and engineering validation:

### A. Pharmacokinetic (PK) Model MVP vs. 2-Compartment Model
* **Current State**: Implemented a **2-compartment pharmacokinetic model** accounting for the absorption delay from subcutaneous tissue (compartment 1) into blood plasma (compartment 2), followed by metabolic hepatic clearance.
* **Uncertainty**: It remains an open clinical question whether a simpler 1-compartment exponential model with a fixed time-to-peak is sufficient for the Minimum Viable Product (MVP), or if the full 2-compartment model is strictly necessary across all patient age groups and BMI strata to prevent dose stacking.
* **Validation Needed**: Clinical microdialysis / subcutaneous pump PK studies comparing observed plasma cortisol curves against 1-compartment vs 2-compartment simulations.

### B. Stress Decay & Recovery Math
* **Current State**: Modeled dynamic stress demands categorized by stress classification:
  1. *Acute physical/emotional stress* (e.g., intense exercise, acute fright): Rapid demand spike with exponential decay.
  2. *Systemic illness / infection* (e.g., gastroenteritis, fever): High, prolonged plateau demand requiring substantial compensatory basal elevation.
* **Uncertainty**: Unlike carbohydrates (which possess well-characterized glycemic indexes and absorption curves), quantifying biometric stress (from HRV, electrodermal activity, skin temperature) into cortisol clearance equivalents is theoretical in current medical literature.
* **Validation Needed**: Prospective observational trials correlating biometric wearable metrics (HRV drop, EDA spikes) with real-time cortisol biosensor declines during controlled stress tests.

### C. Absolute Software Bounds for Automated Delivery
* **Current State**:
  - *Cortisol Sensor Bounds*: Normal range $20–250\text{ ng/mL}$; Crisis warning $< 30\text{ ng/mL}$; Acute over-replacement warning $> 350\text{ ng/mL}$.
  - *Pump Delivery Bounds*: Standard daily replacement $15–25\text{ mg/day}$; Max basal rate default cap $2.0\text{ mg/hr}$; Max acute stress bolus cap $5.0–10.0\text{ mg}$.
  - *Sensitivity*: Default multiplier ~ $25–30\text{ ng/mL}$ rise per $1\text{ mg}$ hydrocortisone for a $70\text{ kg}$ adult.
* **Uncertainty**: Automated subcutaneous hydrocortisone delivery is experimental. Hard-coded software limits must balance preventing adrenal crisis (under-replacement) against preventing acute steroid psychosis / hypertensive crisis (over-replacement).
* **Clinical Safeguard**: Hard bounds must be strictly customizable per patient with mandatory physician override authorization.

---

## 3. Circadian Target Curve Specification
* **Representation**: Discrete time-series setpoints with linear interpolation every minute.
* **Rationale**: Avoids step-change dosing spikes while granting flexibility to shape the steep physiological morning cortisol awakening surge (CAR) and gentle evening slope.
