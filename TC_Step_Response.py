"""
Testfall Template: Regelung Step-Response
==========================================
Prüft die Qualität eines Regelkreises nach einem Sollwertsprung:

    1. Overshoot    : Überschwingung ≤ 10 %
                      overshoot % = (max - setpoint) / setpoint * 100

    2. Abweichung   : Differenz zwischen Sollwert und Istwert ≤ 5 %
                      nach dem Einschwingen (stationärer Fehler)
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------------
CANOE_CONFIG        = "file"
REPORT_PATH         = "C:/Reports/TC_Step_Response_report.txt"

NS_CTRL             = "Control"
VAR_SETPOINT        = "Position_Setpoint_mm"   # Sollwert
VAR_ACTUAL          = "Position_Actual_mm"     # Istwert

SETPOINT_VALUE      = 100.0                    # Sollwertsprung [mm]
MAX_OVERSHOOT_PCT   = 10.0                     # Max Überschwingung [%]
MAX_DEVIATION_PCT   = 5.0                      # Max Abweichung Soll/Ist [%]
RESPONSE_TIME       = 3.0                      # Zeit zum Aufzeichnen der Antwort [s]
SETTLE_TIME         = 3.0                      # Wartezeit bis eingeschwungen [s]
SAMPLE_INTERVAL     = 0.05                     # Abtastzeit [s]

DTC_Signals = [
    "DTC_Overvoltage",
    "DTC_Undervoltage",
    "DTC_CAN_Timeout",
    "DTC_CAN_Failure",
    "DTC_Sensor_Failure",
    "DTC_NVM_Error",
]

HIL = HILTest(CANOE_CONFIG)


# ------------------------------------------------------------------
# Hilfsfunktion: Antwort aufzeichnen
# ------------------------------------------------------------------

def collect_response(duration: float) -> list:
    """Sammelt Istwerte über duration Sekunden. Gibt Liste von Werten zurück."""
    samples = []
    start = time.time()
    while time.time() - start < duration:
        val = HIL.get_system_variable_value(NS_CTRL, VAR_ACTUAL)
        samples.append(val)
        time.sleep(SAMPLE_INTERVAL)
    return samples


# ------------------------------------------------------------------
# TC_STEP_1 — Overshoot ≤ 10 %
# ------------------------------------------------------------------

def TC_STEP_1_overshoot():
    """
    Sollwertsprung 0 → 100 mm.
    Maximale Überschwingung darf 10 % nicht überschreiten.
    Overshoot = (max_Istwert - Sollwert) / Sollwert * 100
    """
    HIL.start_test_case("TC_STEP_1_Overshoot_Max_10_Prozent")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Sollwertsprung
    HIL.set_system_variable_value(NS_CTRL, VAR_SETPOINT, SETPOINT_VALUE)

    # Antwort aufzeichnen
    samples = collect_response(RESPONSE_TIME)

    # Maximalen Istwert finden → Overshoot berechnen
    max_val      = max(samples)
    overshoot_pct = ((max_val - SETPOINT_VALUE) / SETPOINT_VALUE) * 100.0

    # Messwert in Systemvariable schreiben → verify loggt in Report
    HIL.set_system_variable_value("HIL", "Measured_Overshoot_pct", overshoot_pct)
    HIL.verify_system_variable_with_tolerance(
        "HIL", "Measured_Overshoot_pct",
        expected_value=0.0,
        tolerance=MAX_OVERSHOOT_PCT,
    )

    HIL.set_system_variable_value(NS_CTRL, VAR_SETPOINT, 0.0)
    time.sleep(1.0)


# ------------------------------------------------------------------
# TC_STEP_2 — Abweichung Soll/Ist ≤ 5 %
# ------------------------------------------------------------------

def TC_STEP_2_steady_state_deviation():
    """
    Sollwertsprung 0 → 100 mm.
    Nach dem Einschwingen darf die Differenz zwischen Soll- und Istwert
    nicht mehr als 5 % des Sollwerts betragen (stationärer Fehler).
    Abweichung % = |Sollwert - Istwert| / Sollwert * 100
    """
    HIL.start_test_case("TC_STEP_2_Abweichung_Soll_Ist_Max_5_Prozent")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Sollwertsprung
    HIL.set_system_variable_value(NS_CTRL, VAR_SETPOINT, SETPOINT_VALUE)

    # Warten bis System eingeschwungen
    time.sleep(SETTLE_TIME)

    # Istwert nach Einschwingen lesen
    actual_val    = HIL.get_system_variable_value(NS_CTRL, VAR_ACTUAL)
    deviation_pct = (abs(SETPOINT_VALUE - actual_val) / SETPOINT_VALUE) * 100.0

    # Messwert in Systemvariable schreiben → verify loggt in Report
    HIL.set_system_variable_value("HIL", "Measured_Deviation_pct", deviation_pct)
    HIL.verify_system_variable_with_tolerance(
        "HIL", "Measured_Deviation_pct",
        expected_value=0.0,
        tolerance=MAX_DEVIATION_PCT,
    )

    HIL.set_system_variable_value(NS_CTRL, VAR_SETPOINT, 0.0)


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_STEP_1_overshoot()
    TC_STEP_2_steady_state_deviation()

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
