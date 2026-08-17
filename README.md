# AdrenalLoopKit

**AdrenalLoopKit** is a Python library implementing closed-loop automated hormone delivery algorithms for the management of **Primary and Secondary Adrenal Insufficiency (Addison's Disease)**, refactored and adapted from the PyLoopKit model-predictive controller architecture.

---

## Overview & Purpose

Unlike Type 1 Diabetes closed-loop systems that deliver insulin to lower blood glucose, AdrenalLoopKit controls **subcutaneous hydrocortisone (HC) infusions** to maintain physiological **blood cortisol concentrations** across dynamic daily demands.

### Key Architectural & Physiological Features

- **Continuous Cortisol Biosensing**: Ingests real-time wearable sensor cortisol readings ($\text{ng/mL}$).
- **Two-Compartment Pharmacokinetics**: Models subcutaneous depot absorption delay into plasma followed by systemic metabolic clearance, computing active **Hydrocortisone On Board (HOB)**.
- **Positive Hormone Dynamics**: Infusions increase circulating cortisol ($Cortisol(t) = \text{Baseline} + \sum \text{Infusion} \times \text{Sensitivity} \times \text{Decay}(t)$).
- **Circadian Target Curves**: 24-hour diurnal setpoints reflecting natural human cortisol rhythms (steep 4:00–8:00 AM awakening surge, gentle decline to midnight nadir) with minute-level interpolation.
- **Dynamic Stress Load & Demand Modeling**: Quantifies physiological and illness stress disturbances that accelerate cortisol clearance, distinguishing acute physical/emotional stressors from prolonged systemic illness/infection.
- **Safety Bounds & Guardrails**: Hard-coded software delivery limits (max basal rate, max acute bolus cap, sensor crisis thresholds) designed to prevent both life-threatening adrenal crises (under-replacement) and steroid toxicity (over-replacement).

---

## Package Architecture & Core Modules

- [`adrenalloopkit.domain_models`](adrenalloopkit/domain_models.py): Core typed domain classes (`CortisolValue`, `StressLoad`, `InfusionEntry`, `CircadianTargetCurve`, `HydrocortisoneSensitivity`, etc.) with legacy compatibility aliases.
- [`adrenalloopkit.two_compartment_pk_model`](adrenalloopkit/two_compartment_pk_model.py): Subcutaneous-to-plasma 2-compartment pharmacokinetic decay curves.
- [`adrenalloopkit.circadian_curve`](adrenalloopkit/circadian_curve.py): Diurnal circadian target curve interpolation.
- [`adrenalloopkit.hydrocortisone_math`](adrenalloopkit/hydrocortisone_math.py): Active Hydrocortisone On Board (HOB) and predicted cortisol rise effects.
- [`adrenalloopkit.stress_math`](adrenalloopkit/stress_math.py): Dynamic stress load absorption and depletion effects.
- [`adrenalloopkit.infusion_math`](adrenalloopkit/infusion_math.py): Model-predictive dosing engine for recommended temporary basal rates, manual boluses, and autoboluses.
- [`adrenalloopkit.adrenal_data_manager`](adrenalloopkit/adrenal_data_manager.py): Main orchestration pipeline for running algorithm loop updates.

---

## Installation & Environment Setup

AdrenalLoopKit requires **Python 3.7+**.

### 1. Create a Virtual Environment (`venv`)

From the root directory of the repository:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

- **Windows (Command Prompt / PowerShell):**
  ```cmd
  venv\Scripts\activate
  ```

### 3. Install AdrenalLoopKit & Dependencies

Install the package in editable mode for local development:

```bash
pip install --upgrade pip
pip install -e .
```

To deactivate the virtual environment when finished:
```bash
deactivate
```

---

## Running Unit Tests

With the virtual environment activated, run the test suite using Python's built-in `unittest` runner:

```bash
python3 -m unittest discover tests
```

---

## Clinical & Architectural Notes

For detailed documentation on pharmacokinetic modeling choices, stress recovery equations, clinical uncertainty logs, and safety bounds, refer to [`MIGRATION_README.md`](MIGRATION_README.md).
