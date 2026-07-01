"""
Testtemplate: DTC & Fault Injection
=====================================
Dieses File ist ein Template für DTC- und Fault-Injection-Tests.
Als Beispiel wurde ein Overvoltage-Fehler implementiert.

Alle Ergebnisse werden automatisch im Report gespeichert (kein print nötig).
Neue Testfälle können nach demselben Schema hinzugefügt werden.

Testfälle:
    TC_1  Fault Injection Overvoltage → DTC_Signal_OV wird ausgelöst
    TC_2  Ignition OFF/ON             → DTC_Signal_OV ist nicht mehr aktiv
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration  (an Projekt anpassen)
# ------------------------------------------------------------------
CANOE_CONFIG = "file"                    # Pfad zur CANoe .cfg Datei
REPORT_PATH  = "C:/Reports/DTC_report.txt"

OVERVOLTAGE_VALUE = 1                    # Wert zum Aktivieren des Overvoltage-Fehlers
DTC_TIMEOUT_S     = 5.0                  # Maximale Zeit bis DTC ausgelöst wird [s]
IGNITION_WAIT_S   = 1.0                  # Wartezeit nach Ignition OFF [s]
ECU_BOOT_TIMEOUT  = 5.0                  # Maximale Wartezeit bis ECU bereit [s]
OPERATION_MODE    = 4                    # ECU Normal-Betriebsmodus

# Liste aller DTCs die vor jedem Test inaktiv sein müssen (Precondition)
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
# TC_1 — Fault Injection Overvoltage → DTC muss ausgelöst werden
# ------------------------------------------------------------------

def TC_1():
    """
    Ziel: Overvoltage-Fehler injizieren und prüfen ob DTC_Signal_OV
          innerhalb der definierten Zeit ausgelöst wird.
    """
    HIL.start_test_case("TC_1_Fault_Injection_Overvoltage")

    # Precondition: ECU im Normalbetrieb, keine aktiven DTCs
    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Fault Injection: Overvoltage aktivieren
    HIL.set_system_variable_value("Fault_Injection", "Overvoltage", OVERVOLTAGE_VALUE)

    # Prüfen: DTC_Signal_OV muss innerhalb DTC_TIMEOUT_S auf 1 gehen
    HIL.wait_for_system_variable("DTC", "DTC_Signal_OV", 1, DTC_TIMEOUT_S)

    # Fault Injection zurücksetzen
    HIL.set_system_variable_value("Fault_Injection", "Overvoltage", 0)


# ------------------------------------------------------------------
# TC_2 — Ignition OFF/ON → DTC darf nicht mehr aktiv sein
# ------------------------------------------------------------------

def TC_2():
    """
    Ziel: Nach Ignition OFF → ON muss DTC_Signal_OV inaktiv (0) sein.
    Prüft ob DTCs beim Neustart korrekt zurückgesetzt werden.
    """
    HIL.start_test_case("TC_2_DTC_Reset_Nach_Ignition_Cycle")

    # Ignition OFF
    HIL.set_environment_variable_value("IgnitionState", 0)
    time.sleep(IGNITION_WAIT_S)          # ECU vollständig herunterfahren lassen

    # Ignition ON
    HIL.set_environment_variable_value("IgnitionState", 1)

    # Warten bis ECU wieder im Normalbetrieb (Operation Mode 4)
    HIL.wait_for_system_variable("STATE", "STATE", OPERATION_MODE, ECU_BOOT_TIMEOUT)

    # Prüfen: DTC muss nach Neustart inaktiv sein (== 0)
    HIL.verify_system_variable_with_tolerance("DTC", "DTC_Signal_OV",
                                              expected_value=0, tolerance=0)


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_1()
    TC_2()                               # Fehler war: TC_2 ohne () → wurde nie aufgerufen

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
