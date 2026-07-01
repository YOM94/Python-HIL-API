# Python HIL Test Framework — CANoe

A Python-based Hardware-In-the-Loop (HIL) test framework for automotive software validation using Vector CANoe.

## Overview

This framework provides reusable test utilities for automotive ECU testing via CAN bus. It wraps the `py_canoe` API and adds structured test reporting, signal verification, fault injection, and interpolation-based validation.

---

## Features

| Feature | Description |
|---|---|
| CAN Signal Access | Read / write CAN signals and system variables |
| Environment Variables | Control CANoe panel inputs (ignition, fault simulation) |
| Polling with Timeout | Wait for signals or variables to reach expected values |
| Tolerance Verification | Verify values within defined tolerances |
| ADC Verification | Validate ADC values using linear formula or calibration table |
| 1D Interpolation | Linear lookup-table interpolation (ECU characteristic curves) |
| Fault Injection | Inject hardware faults via system variables |
| NVM Testing | Verify non-volatile memory persistence across power cycles |
| Semi-Automated Tests | Pause for manual intervention (cable disconnect, sensor removal) |
| Test Reporting | Automatic PASS/FAIL report generated as `.txt` file |

---

## Project Structure

```
Python-HIL-API/
├── HIL_Test.py                  # Core framework class (HILTest)
├── TC_BrakeRequest_Mapping.py   # Brake force mapping tests (E2E, timeout, scaling)
├── DTC_Template.py              # DTC & Fault Injection test template
├── ADC_Test.py                  # ADC linearity verification (12-bit)
├── NVM_Test.py                  # NVM persistence across ignition and battery cycles
└── Semi_Automated_Test.py       # Semi-automated hardware failure tests
```

---

## Technologies

- **Python 3.x**
- **Vector CANoe** via `py_canoe`
- **CAN Bus** (automotive communication)
- **AUTOSAR** concepts (E2E protection, DTC, Safe State, NVM)
- **HIL Testing** methodology

---

## Test Cases

### Brake Force Mapping (`TC_BrakeRequest_Mapping.py`)
Tests the mapping from potentiometer voltage (0–5 V) to clamping force (0–30 000 N):
- Minimum and maximum boundary values
- Linear scaling at multiple breakpoints using interpolation
- Upper boundary clamp behavior
- E2E protection error handling
- CAN timeout detection

### ADC Verification (`ADC_Test.py`)
Validates 12-bit ADC linearity using the formula:
```
ADC_expected = (Voltage / 5.0) * 4095
```

### NVM Persistence (`NVM_Test.py`)
Verifies that `Brake_Force` is correctly stored in non-volatile memory:
- Ignition cycle test (automatic)
- Multiple value test: 0 N / 15 000 N / 30 000 N
- Battery disconnect test (semi-automatic)

### DTC & Fault Injection (`DTC_Template.py`)
Template for fault injection tests:
- Overvoltage fault → DTC triggered within timeout
- Ignition OFF/ON → DTC reset verification

### Semi-Automated Tests (`Semi_Automated_Test.py`)
Tests requiring physical intervention:
- CAN cable disconnect → DTC_CAN_Failure
- Sensor disconnect → DTC_Sensor_Fail

---

## Report Example

```
========================================================================
TEST REPORT  —  HIL Test Framework
Generated : 2026-06-29  14:30:00
Config    : C:/CANoe/BrakeProject/BrakeSystem.cfg
========================================================================

TEST CASE: TC_1_Fault_Injection_Overvoltage
Start: 14:30:01.123
------------------------------------------------------------------------
[14:30:01.130] [INFO]  SET SysVar       | Fault_Injection::Overvoltage = 1
[14:30:03.210] [PASS]  WAIT SysVar      | DTC::DTC_Signal_OV == 1  (timeout: 5.0s)
[14:30:03.215] [INFO]  SET SysVar       | Fault_Injection::Overvoltage = 0
End:    14:30:03.220
Result: PASS  (1 passed, 0 failed)
========================================================================
```

---

## Installation

```bash
pip install py_canoe
```

---

## Usage

```python
from HIL_Test import HILTest

hil = HILTest("C:/CANoe/MyProject.cfg")

try:
    hil.start_test_case("TC_001_Example")
    hil.set_signal_value("CAN 1", "BrakeControl", "BrakeRequest", 50.0)
    hil.verify_system_variable_with_tolerance("BrakeSystem", "ClampForce_N",
                                               expected_value=15000, tolerance=150)
finally:
    hil.save_report("C:/Reports/report.txt")
    hil.close()
```

---

## Author

Youssef Marfoq
