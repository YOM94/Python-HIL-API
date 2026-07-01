"""
Test Cases: Bremswunsch → Soll-Klemmkraft Mapping
==================================================

Requirement:
    Das System empfängt den Bremswunsch als E2E-geschütztes CAN-Signal
    (Wertebereich + Skalierung definiert) und bildet ihn auf eine
    Soll-Klemmkraft im Bereich 0…30 000 N ab.

Physikalische Kette:
    Potentiometer (0…5 V)
        → ADC (0…4095)
            → CAN-Signal BrakeRequest (Bremswunsch)
                → ECU
                    → Soll-Klemmkraft (0…30 000 N)

Skalierung (linear, zwei Stufen):
    Stufe 1  Spannung → Klemmkraft : 0 V = 0 N,  5 V = 30 000 N
             ClampForce_N = (Voltage / 5.0) * 30 000

Annahmen (an echte DBC / Spezifikation anpassen):
    Spannungseingang  : Systemvariable  HIL::PotiVoltage_V   [0…5 V]
    CAN-Ausgangssignal: CAN 1 :: BrakeControl :: BrakeRequest (wird von ECU empfangen)
    Klemmkraft-Ausgang: Systemvariable  BrakeSystem::ClampForce_N  [0…30 000 N]
    Toleranz          : ±150 N  (0.5 % von 30 000 N)

Testfälle:
    TC_001  Minimum-Spannung   (0.0 V)  →   0 N
    TC_002  Maximum-Spannung   (5.0 V)  →  30 000 N
    TC_003  Skalierung linear  (Stützpunkte 1 V / 2.5 V / 4 V)
    TC_004  Grenzwert oben     (Spannung > 5 V)  →  Clamp auf 30 000 N
    TC_005  E2E-Fehler         →  Klemmkraft bleibt auf letztem gültigen Wert
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration  (an Projekt anpassen)
# ------------------------------------------------------------------
CANOE_CONFIG = "C:/CANoe/BrakeProject/BrakeSystem.cfg"
REPORT_PATH  = "C:/Reports/TC_BrakeRequest_Mapping_report.txt"

# Potentiometer-Spannung (HIL-Eingang)
NS_HIL       = "HIL"
VAR_VOLTAGE  = "PotiVoltage_V"           # Spannung in Volt [0…5 V]
VOLTAGE_MAX  = 5.0

# Klemmkraft-Ausgang (ECU-Ausgang)
NS_BRAKE     = "BrakeSystem"
VAR_CLAMP    = "ClampForce_N"            # Soll-Klemmkraft in Newton [0…30 000 N]
CLAMP_MAX_N  = 30_000

TOLERANCE_N  = 150                       # ±150 N zulässige Abweichung
SETTLE_TIME  = 0.1                       # Wartezeit nach Spannungsänderung [s]

# Referenz-Lookup-Table: Spannung [V] → Klemmkraft [N]  (linear)
SCALING_VOLT = [0.0,  1.0,     2.5,     4.0,     5.0]
SCALING_N    = [0,    6_000,   15_000,  24_000,  30_000]

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

def set_voltage(hil: HILTest, volts: float):
    """Setzt die Potentiometer-Spannung über die HIL-Systemvariable."""
    hil.set_system_variable_value(NS_HIL, VAR_VOLTAGE, volts)
    time.sleep(SETTLE_TIME)


def verify_clamp(hil: HILTest, expected_n: float) -> bool:
    """Prüft ob die Klemmkraft innerhalb ±TOLERANCE_N liegt."""
    return hil.verify_system_variable_with_tolerance(
        NS_BRAKE, VAR_CLAMP, expected_n, TOLERANCE_N
    )


# ------------------------------------------------------------------
# TC_001 — Minimum-Spannung: 0 V → 0 N
# ------------------------------------------------------------------

def TC_001_minimum_voltage(hil: HILTest):
    """
    Ziel : Spannung = 0 V  →  Klemmkraft = 0 N.
    Prüft den unteren Grenzwert des Wertebereichs.
    """
    hil.start_test_case("TC_001_Minimum_Spannung_0V")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    set_voltage(hil, 0.0)
    verify_clamp(hil, expected_n=0)


# ------------------------------------------------------------------
# TC_002 — Maximum-Spannung: 5 V → 30 000 N
# ------------------------------------------------------------------

def TC_002_maximum_voltage(hil: HILTest):
    """
    Ziel : Spannung = 5 V  →  Klemmkraft = 30 000 N.
    Prüft den oberen Grenzwert des Wertebereichs.
    """
    hil.start_test_case("TC_002_Maximum_Spannung_5V")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    set_voltage(hil, 5.0)
    verify_clamp(hil, expected_n=CLAMP_MAX_N)


# ------------------------------------------------------------------
# TC_003 — Skalierung: Stützpunkte 1 V / 2.5 V / 4 V
# ------------------------------------------------------------------

def TC_003_scaling_verification(hil: HILTest):
    """
    Ziel : Lineare Skalierung zwischen 0 V und 5 V prüfen.
    Der Sollwert wird per Interpolation aus der Referenztabelle berechnet
    und mit dem ECU-Ausgangswert verglichen.
    """
    hil.start_test_case("TC_003_Skalierung_Spannung_zu_Klemmkraft")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    test_voltages = [1.0, 2.5, 4.0]

    for volt in test_voltages:
        expected_n = HILTest.interpolate(SCALING_VOLT, SCALING_N, volt)
        set_voltage(hil, volt)
        verify_clamp(hil, expected_n=expected_n)

    # Zurück auf 0 V nach dem Test
    set_voltage(hil, 0.0)


# ------------------------------------------------------------------
# TC_004 — Grenzwert oben: Spannung > 5 V → Clamp auf 30 000 N
# ------------------------------------------------------------------

def TC_004_upper_boundary_clamp(hil: HILTest):
    """
    Ziel : Spannung über dem definierten Wertebereich (z. B. 5.5 V)
    darf die Klemmkraft nicht über 30 000 N treiben (Clamp-Verhalten der ECU).
    """
    hil.start_test_case("TC_004_Spannung_Ueber_Bereich_5V5")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    set_voltage(hil, 5.5)
    # ECU muss auf Maximum klemmen, kein Überschwingen
    verify_clamp(hil, expected_n=CLAMP_MAX_N)

    set_voltage(hil, 0.0)


# ------------------------------------------------------------------
# TC_005 — E2E-Fehler: Klemmkraft bleibt auf letztem gültigen Wert
# ------------------------------------------------------------------

def TC_005_e2e_error_handling(hil: HILTest):
    """
    Ziel : Bei ungültigem E2E-Schutz (falscher CRC oder Counter-Fehler)
    darf die ECU das neue CAN-Signal NICHT übernehmen.
    Die Klemmkraft muss auf dem letzten gültigen Wert eingefroren bleiben.

    Ablauf:
      1. Gültige Spannung (2.5 V) setzen  →  15 000 N eingefroren
      2. E2E-Fehler simulieren
      3. Neue Spannung (4.0 V) setzen      →  Klemmkraft MUSS bei 15 000 N bleiben
    """
    hil.start_test_case("TC_005_E2E_Fehler_Handling")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    # Schritt 1: Gültigen Zustand herstellen
    hil.set_environment_variable_value("E2E_ErrorSimulation", 0)   # E2E gültig
    set_voltage(hil, 2.5)
    verify_clamp(hil, expected_n=15_000)

    # Schritt 2: E2E-Fehler aktivieren (über CANoe-Umgebungsvariable)
    hil.set_environment_variable_value("E2E_ErrorSimulation", 1)
    time.sleep(0.05)

    # Schritt 3: Neue Spannung setzen — ECU darf CAN-Signal NICHT akzeptieren
    set_voltage(hil, 4.0)
    # Klemmkraft muss noch 15 000 N sein (letzter gültiger Wert)
    verify_clamp(hil, expected_n=15_000)

    # Aufräumen
    hil.set_environment_variable_value("E2E_ErrorSimulation", 0)
    set_voltage(hil, 0.0)


# ------------------------------------------------------------------
# Hauptprogramm — alle TCs ausführen
# ------------------------------------------------------------------

def main():
    hil = HILTest(CANOE_CONFIG)

    try:
        TC_001_minimum_voltage(hil)
        TC_002_maximum_voltage(hil)
        TC_003_scaling_verification(hil)
        TC_004_upper_boundary_clamp(hil)
        TC_005_e2e_error_handling(hil)

    finally:
        hil.save_report(REPORT_PATH)
        hil.close()
        print(f"Report gespeichert: {REPORT_PATH}")


if __name__ == "__main__":
    main()
