"""
Testfall: Kaskaden-Regelung Verifikation
=========================================
Idee:
    Positiv: Position setzen + Strom & Drehzahl aktiv  → Position wird erreicht
    Negativ: Position setzen + Strom & Drehzahl deaktiviert → Position wird NICHT erreicht

    Beweist dass der Positionsregler von den inneren Kreisen abhängt.
    Wenn Position ohne Strom/Drehzahl erreicht wird → Kaskade falsch implementiert!
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------------
CANOE_CONFIG        = "file"
REPORT_PATH         = "C:/Reports/TC_Cascade_Control_report.txt"

NS_CTRL             = "Control"
VAR_POS_SETPOINT    = "Position_Setpoint_mm"
VAR_POS_ACTUAL      = "Position_Actual_mm"
VAR_SPEED_ACTUAL    = "Speed_Actual_rpm"
VAR_CURRENT_ACTUAL  = "Current_Actual_A"

NS_FAULT            = "Fault_Injection"
VAR_DISABLE_SPEED   = "Disable_Speed_Loop"
VAR_DISABLE_CURR    = "Disable_Current_Loop"

POSITION_TARGET     = 100.0             # Sollposition [mm]
POSITION_TOLERANCE  = 1.0              # ±1 mm für Positiv-Test
POSITION_MAX_NEG    = 5.0              # Max erlaubte Bewegung im Negativ-Test [mm]
SETTLE_TIME         = 3.0              # Wartezeit bis System eingeschwungen [s]

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
# TC_CASCADE_1 — Positiv: alle Kreise aktiv → Position wird erreicht
# ------------------------------------------------------------------

def TC_CASCADE_1_positive():
    """
    Alle drei Regelkreise aktiv.
    Sollposition = 100 mm → muss nach SETTLE_TIME erreicht sein.
    """
    HIL.start_test_case("TC_CASCADE_1_Positiv_Alle_Kreise_Aktiv")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Alle Kreise aktivieren
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_CURR,  0)
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_SPEED, 0)

    # Sollposition setzen
    HIL.set_system_variable_value(NS_CTRL, VAR_POS_SETPOINT, POSITION_TARGET)
    time.sleep(SETTLE_TIME)

    # Position muss erreicht sein
    HIL.verify_system_variable_with_tolerance(
        NS_CTRL, VAR_POS_ACTUAL,
        expected_value=POSITION_TARGET,
        tolerance=POSITION_TOLERANCE,
    )

    # Zurücksetzen
    HIL.set_system_variable_value(NS_CTRL, VAR_POS_SETPOINT, 0.0)
    time.sleep(1.0)


# ------------------------------------------------------------------
# TC_CASCADE_2 — Negativ: kein Strom, keine Drehzahl → keine Position
# ------------------------------------------------------------------

def TC_CASCADE_2_negative():
    """
    Strom- und Drehzahlregler deaktiviert.
    Sollposition = 100 mm gesetzt → Position darf NICHT erreicht werden.
    Strom und Drehzahl müssen bei 0 bleiben.
    """
    HIL.start_test_case("TC_CASCADE_2_Negativ_Kein_Strom_Keine_Drehzahl")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Innere Kreise deaktivieren
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_CURR,  1)
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_SPEED, 1)

    # Sollposition setzen
    HIL.set_system_variable_value(NS_CTRL, VAR_POS_SETPOINT, POSITION_TARGET)
    time.sleep(SETTLE_TIME)

    # Position darf NICHT erreicht sein
    HIL.verify_system_variable_with_tolerance(
        NS_CTRL, VAR_POS_ACTUAL,
        expected_value=0.0,
        tolerance=POSITION_MAX_NEG,
    )

    # Drehzahl muss 0 sein
    HIL.verify_system_variable_with_tolerance(
        NS_CTRL, VAR_SPEED_ACTUAL,
        expected_value=0.0,
        tolerance=10.0,
    )

    # Strom muss 0 sein
    HIL.verify_system_variable_with_tolerance(
        NS_CTRL, VAR_CURRENT_ACTUAL,
        expected_value=0.0,
        tolerance=0.1,
    )

    # Aufräumen
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_CURR,  0)
    HIL.set_system_variable_value(NS_FAULT, VAR_DISABLE_SPEED, 0)
    HIL.set_system_variable_value(NS_CTRL,  VAR_POS_SETPOINT,  0.0)


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_CASCADE_1_positive()
    TC_CASCADE_2_negative()

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
