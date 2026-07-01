"""
Semi-Automated Test: Hardware-Fehler → DTC Verifikation
=========================================================
Ablauf:
    1. Tester trennt Kabel oder Sensor physisch
    2. Python prüft automatisch ob der erwartete DTC gesetzt wurde

Testfälle:
    TC_SA_1  CAN-Kabel trennen  → DTC_CAN_Failure muss aktiv sein
    TC_SA_2  Sensor abstecken   → DTC_Sensor_Fail muss aktiv sein
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration  (an Projekt anpassen)
# ------------------------------------------------------------------
CANOE_CONFIG     = "file"
REPORT_PATH      = "C:/Reports/Semi_Automated_report.txt"

NS_DTC           = "DTC"
DTC_CAN_FAILURE  = "DTC_CAN_Failure"
DTC_SENSOR_FAIL  = "DTC_Sensor_Fail"

REACTION_TIMEOUT = 5.0                  # Maximale Zeit bis DTC gesetzt wird [s]

DTC_Signals = [DTC_CAN_FAILURE, DTC_SENSOR_FAIL]

HIL = HILTest(CANOE_CONFIG)


# ------------------------------------------------------------------
# TC_SA_1 — CAN-Kabel trennen → DTC_CAN_Failure
# ------------------------------------------------------------------

def TC_SA_1_can_cable_disconnect():
    """
    Tester trennt das CAN-Kabel.
    Python prüft ob DTC_CAN_Failure innerhalb REACTION_TIMEOUT gesetzt wird.
    """
    HIL.start_test_case("TC_SA_1_CAN_Kabel_Trennen")

    # Precondition: Normalbetrieb, keine aktiven DTCs
    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Tester trennt Kabel physisch
    HIL.wait_for_test_completion(
        prompt="\n>>> AKTION: Bitte CAN-Kabel (CAN 1) vom Steuergerät trennen.\n"
               "    Danach 'yes' eingeben und ENTER drücken: "
    )

    # DTC_CAN_Failure muss innerhalb REACTION_TIMEOUT auf 1 gehen
    HIL.wait_for_system_variable(
        NS_DTC, DTC_CAN_FAILURE, expected_value=1, timeout=REACTION_TIMEOUT
    )


# ------------------------------------------------------------------
# TC_SA_2 — Sensor abstecken → DTC_Sensor_Fail
# ------------------------------------------------------------------

def TC_SA_2_sensor_disconnect():
    """
    Tester steckt den Sensor-Stecker ab.
    Python prüft ob DTC_Sensor_Fail innerhalb REACTION_TIMEOUT gesetzt wird.
    """
    HIL.start_test_case("TC_SA_2_Sensor_Abstecken")

    # Precondition: Normalbetrieb, keine aktiven DTCs
    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Tester steckt Sensor ab
    HIL.wait_for_test_completion(
        prompt="\n>>> AKTION: Bitte Sensor-Stecker abstecken.\n"
               "    Danach 'yes' eingeben und ENTER drücken: "
    )

    # DTC_Sensor_Fail muss innerhalb REACTION_TIMEOUT auf 1 gehen
    HIL.wait_for_system_variable(
        NS_DTC, DTC_SENSOR_FAIL, expected_value=1, timeout=REACTION_TIMEOUT
    )


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_SA_1_can_cable_disconnect()
    TC_SA_2_sensor_disconnect()

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
