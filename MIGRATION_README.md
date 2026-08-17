# AdrenalLoopKit Migration & Architectural Readiness Log

This document serves as a living log of architectural decisions, physiological models, clinical safety considerations, and known unknowns for the development and clinical team.

---

## 1. Domain Overview & Scope Transition

AdrenalLoopKit is a closed-loop automated hormone delivery algorithm designed specifically for the management of **Primary and Secondary Adrenal Insufficiency (Addison's Disease)**, refactored from the PyLoopKit model-predictive controller architecture.

### Domain & Code Migration Mapping

| PyLoopKit (Diabetes) | AdrenalLoopKit (Addison's) | Units / Representation | Physiological Mechanism & Implementation |
| :--- | :--- | :--- | :--- |
| `GlucoseValue` | `CortisolValue` | Float ($\text{ng/mL}$) | Continuous wearable biosensor cortisol readings ($10\text{ ng/mL} = 1\ \mu\text{g/dL}$). |
| `CarbEntry` | `StressLoad` | Integer / Index | Active disturbance causing increased physiological demand / rapid cortisol depletion. |
| `DoseEntry` (Insulin) | `InfusionEntry` (HC) | Float ($\text{mg}$ / $\mu\text{g}$) | Hormone replacement delivered continuously via subcutaneous infusion pump ($1\text{ mg} = 1000\ \mu\text{g}$). |
| `InsulinOnBoard` (`IOB`) | `HydrocortisoneOnBoard` (`HOB`) | Float ($\text{mg}$) | Active circulating / remaining hydrocortisone tracking across the 2-compartment decay timeline. |
| `TargetRange` | `CircadianTargetCurve` | Time-series array | Asymmetric 24-hour diurnal rhythm (early morning awakening spike 4:00–8:00 AM, gradual decline to midnight nadir). |
| `InsulinSensitivityFactor` | `HydrocortisoneSensitivity` | Multiplier ($\text{ng/mL}$ per $\text{mg}$) | Expected rise in blood cortisol concentration per $1\text{ mg}$ hydrocortisone ($Cortisol(t) = \text{Baseline} + \sum \text{Infusion} \times \text{Sens} \times \text{Decay}(t)$). |

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

AdrenalLoopKit implements dynamic 24-hour target curve modeling through both continuous mathematical evaluation (`CircadianTargetGenerator`) and discrete setpoint linear interpolation (`CircadianCurveInterpolator`):

### Continuous Mathematical Model (`CircadianTargetGenerator`)
* **Wake-Time Parameterization**: Curves are anchored dynamically to the patient's habitual wake time ($T_{\text{wake}}$, default `06:00`), supporting custom schedules and shift-work adjustments.
* **Diurnal Phases & Formulation**:
  1. **Morning Awakening Surge ($[T_{\text{wake}} - 3\text{h}, T_{\text{wake}}]$)**: Aggressive exponential ramp modeling the physiological Cortisol Awakening Response (CAR) from nocturnal nadir baseline to morning peak:
     $$C(u) = C_{\text{base}} + (C_{\text{peak}} - C_{\text{base}}) \cdot \frac{e^{k \cdot u} - 1}{e^k - 1}, \quad u = \frac{t_{\text{rel}} + 3}{3} \in [0, 1]$$
  2. **Daytime Linear Taper ($[T_{\text{wake}}, T_{\text{wake}} + 8\text{h}]$)**: Gradual linear descent from morning peak down to mid-afternoon target:
     $$C(u) = C_{\text{peak}} - u \cdot (C_{\text{peak}} - C_{\text{afternoon}}), \quad u = \frac{t_{\text{rel}}}{8} \in [0, 1]$$
  3. **Evening Flattening Taper ($[T_{\text{wake}} + 8\text{h}, T_{\text{wake}} + 17\text{h}]$)**: Quadratic asymptotic decay smoothly flattening into nocturnal baseline ($\frac{dC}{du} = 0$ at $u=1$):
     $$C(u) = C_{\text{base}} + (C_{\text{afternoon}} - C_{\text{base}}) \cdot (1 - u)^2, \quad u = \frac{t_{\text{rel}} - 8}{9} \in [0, 1]$$
  4. **Nocturnal Sleep Baseline ($[T_{\text{wake}} + 17\text{h}, T_{\text{wake}} - 3\text{h}]$)**: Stable physiological nadir target ($C(t) = C_{\text{base}}$).
* **System Clock Polling**: Exposes `target_value_at(time)` for continuous target evaluation and `target_at_time(time)` for symmetric safety band generation (`[min_target, max_target]`).

