"""
Test: NVM Persistenz — Brake_Force Variable
=============================================
Ziel:
    Prüfen ob die Variable Brake_Force nach einem Power-Cycle
    (Ignition OFF → ON oder Batterie trennen) noch korrekt
    im NVM gespeichert ist.

Testvarianten:
    TC_NVM_1  Ignition-Zyklus        → vollautomatisch
    TC_NVM_2  Mehrere Werte          → vollautomatisch (0 N, 15 000 N, 30 000 N)
    TC_NVM_3  Batterie trennen       → semiautomatisch (physischer Eingriff)
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration  (an Projekt anpassen)
# ------------------------------------------------------------------
CANOE_CONFIG      = "file"
REPORT_PATH       = "C:/Reports/NVM_Test_report.txt"

NS_BRAKE          = "BrakeSystem"
VAR_BRAKE_FORCE   = "Brake_Force"       # NVM-Variable die getestet wird

NS_STATE          = "STATE"
VAR_STATE         = "STATE"
OPERATION_MODE    = 4                   # Normalbetrieb

IGNITION_OFF_WAIT = 1.0                 # Wartezeit nach Ignition OFF [s]
ECU_BOOT_TIMEOUT  = 5.0                 # Maximale Wartezeit bis ECU bereit [s]
TOLERANCE_N       = 0                   # NVM-Wert muss exakt stimmen

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
# Hilfsfunktionen
# ------------------------------------------------------------------

def set_brake_force(value: float):
    """Setzt Brake_Force und wartet kurz damit NVM schreiben kann."""
    HIL.set_system_variable_value(NS_BRAKE, VAR_BRAKE_FORCE, value)
    time.sleep(0.2)                     # ECU braucht Zeit um NVM zu beschreiben


def ignition_cycle():
    """Ignition OFF → warten → ON → warten bis ECU bereit."""
    HIL.set_environment_variable_value("IgnitionState", 0)
    time.sleep(IGNITION_OFF_WAIT)
    HIL.set_environment_variable_value("IgnitionState", 1)
    HIL.wait_for_system_variable(NS_STATE, VAR_STATE, OPERATION_MODE, ECU_BOOT_TIMEOUT)


def verify_brake_force(expected_value: float):
    """Liest Brake_Force und prüft ob der Wert mit dem gespeicherten übereinstimmt."""
    HIL.verify_system_variable_with_tolerance(
        NS_BRAKE, VAR_BRAKE_FORCE,
        expected_value=expected_value,
        tolerance=TOLERANCE_N,
    )


# ------------------------------------------------------------------
# TC_NVM_1 — Ignition-Zyklus: ein Wert wird gespeichert und geprüft
# ------------------------------------------------------------------

def TC_NVM_1_ignition_cycle():
    """
    Ablauf:
      1. Brake_Force = 15 000 N setzen (NVM beschreiben)
      2. Ignition OFF → ON
      3. Brake_Force lesen → muss noch 15 000 N sein
    """
    HIL.start_test_case("TC_NVM_1_Ignition_Zyklus")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Schritt 1: Wert in NVM schreiben
    set_brake_force(15_000)

    # Schritt 2: Ignition OFF → ON (Strom weg → NVM muss Wert halten)
    ignition_cycle()

    # Schritt 3: Wert nach Neustart prüfen
    verify_brake_force(expected_value=15_000)


# ------------------------------------------------------------------
# TC_NVM_2 — Mehrere Werte: 0 N, 15 000 N, 30 000 N
# ------------------------------------------------------------------

def TC_NVM_2_multiple_values():
    """
    Ablauf:
      Für jeden Wert in TEST_VALUES:
        1. Brake_Force setzen
        2. Ignition OFF → ON
        3. Brake_Force muss nach Neustart gleich sein

    Sichert dass NVM nicht nur einen fixen Wert speichert.
    """
    HIL.start_test_case("TC_NVM_2_Mehrere_Werte_0_15000_30000")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    test_values = [0, 15_000, 30_000]

    for value in test_values:
        # Wert setzen
        set_brake_force(value)

        # Power Cycle
        ignition_cycle()

        # NVM-Wert prüfen
        verify_brake_force(expected_value=value)


# ------------------------------------------------------------------
# TC_NVM_3 — Batterie trennen: echter Stromverlust (semiautomatisch)
# ------------------------------------------------------------------

def TC_NVM_3_battery_disconnect():
    """
    Ablauf:
      1. Brake_Force = 25 000 N setzen
      2. Tester trennt Batterie physisch (echter Stromverlust)
      3. Tester klemmt Batterie wieder an
      4. Brake_Force muss noch 25 000 N sein

    Unterschied zu TC_NVM_1: Batterie-Trennung ist ein härterer Test
    als Ignition-Zyklus — prüft ob NVM auch bei komplettem Stromverlust hält.
    """
    HIL.start_test_case("TC_NVM_3_Batterie_Trennen_Semiautomatisch")

    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    # Schritt 1: Wert setzen
    set_brake_force(25_000)

    # Schritt 2: Tester trennt Batterie
    HIL.wait_for_test_completion(
        prompt="\n>>> AKTION: Bitte Batterie (Klemme 30) trennen.\n"
               "    5 Sekunden warten, dann wieder anklemmen.\n"
               "    Danach 'yes' eingeben und ENTER drücken: "
    )

    # Warten bis ECU nach Battery-Connect wieder bereit ist
    HIL.wait_for_system_variable(NS_STATE, VAR_STATE, OPERATION_MODE, ECU_BOOT_TIMEOUT)

    # Schritt 3: NVM-Wert nach echtem Stromverlust prüfen
    verify_brake_force(expected_value=25_000)


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_NVM_1_ignition_cycle()
    TC_NVM_2_multiple_values()
    TC_NVM_3_battery_disconnect()

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
