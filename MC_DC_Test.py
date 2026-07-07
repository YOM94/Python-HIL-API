"""
MC/DC Test: Signal_A..Signal_D -> Flag
=======================================

Requirement:
    Wenn eines der Signale Signal_A, Signal_B, Signal_C, Signal_D groesser
    als 10 ist, dann ist Flag = True, sonst Flag = False.

    Flag = (Signal_A > 10) or (Signal_B > 10) or (Signal_C > 10) or (Signal_D > 10)

    Signal_A..Signal_D und Flag sind CANoe-Systemvariablen.

MC/DC-Herleitung (4 Bedingungen, reine ODER-Verknuepfung):
    -> 5 MC/DC-Testfaelle statt 16 bei voller Wahrheitstabelle (2^4)

    Testfall |  A  |  B  |  C  |  D  | erwartetes Flag | zeigt Unabhaengigkeit von
    ---------+-----+-----+-----+-----+------------------+---------------------------
    T1       |  F  |  F  |  F  |  F  |  False           | Baseline
    T2       |  T  |  F  |  F  |  F  |  True            | Signal_A  (T1 vs T2)
    T3       |  F  |  T  |  F  |  F  |  True            | Signal_B  (T1 vs T3)
    T4       |  F  |  F  |  T  |  F  |  True            | Signal_C  (T1 vs T4)
    T5       |  F  |  F  |  F  |  T  |  True            | Signal_D  (T1 vs T5)

    T = > 10 (SIGNAL_TRUE_VALUE), F = <= 10 (SIGNAL_FALSE_VALUE).
    Jedes Testpaar (T1 vs T2..T5) unterscheidet sich in genau einem Signal
    UND das Ergebnis kippt -> das ist die MC/DC-Unabhaengigkeitsbedingung.

Testablauf je Testfall:
    1. Vollstaendigen Eingangsvektor (A, B, C, D) explizit setzen
    2. Flag verifizieren
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration  (an Projekt anpassen)
# ------------------------------------------------------------------
CANOE_CONFIG = "file"
REPORT_PATH  = "C:/Reports/MC_DC_Test_report.txt"

NS_SIGNAL          = "IO"      # Namespace der Signal_A..Signal_D Systemvariablen
NS_FLAG            = "IO"      # Namespace der Flag Systemvariable
VAR_FLAG           = "Flag"

THRESHOLD          = 10
SIGNAL_TRUE_VALUE  = 15        # > THRESHOLD  -> Bedingung TRUE
SIGNAL_FALSE_VALUE = 0         # <= THRESHOLD -> Bedingung FALSE
FLAG_TRUE          = 1
FLAG_FALSE         = 0
SETTLE_TIME        = 0.1       # Wartezeit nach Signaenderung [s]

# MC/DC-Testfaelle: (Testfall-ID, Vektor {Signalname: True/False}, erwartetes Flag, Beschreibung)
# True = >10, False = <=10.
TEST_CASES = [
    ("T1", {"Signal_A": False, "Signal_B": False, "Signal_C": False, "Signal_D": False},
        FLAG_FALSE, "Baseline: alle Signale <= 10"),
    ("T2", {"Signal_A": True,  "Signal_B": False, "Signal_C": False, "Signal_D": False},
        FLAG_TRUE, "Signal_A > 10, Rest <= 10 (Unabhaengigkeit Signal_A, vgl. T1)"),
    ("T3", {"Signal_A": False, "Signal_B": True,  "Signal_C": False, "Signal_D": False},
        FLAG_TRUE, "Signal_B > 10, Rest <= 10 (Unabhaengigkeit Signal_B, vgl. T1)"),
    ("T4", {"Signal_A": False, "Signal_B": False, "Signal_C": True,  "Signal_D": False},
        FLAG_TRUE, "Signal_C > 10, Rest <= 10 (Unabhaengigkeit Signal_C, vgl. T1)"),
    ("T5", {"Signal_A": False, "Signal_B": False, "Signal_C": False, "Signal_D": True },
        FLAG_TRUE, "Signal_D > 10, Rest <= 10 (Unabhaengigkeit Signal_D, vgl. T1)"),
]

DTC_Signals = [
    "DTC_Overvoltage",
    "DTC_Undervoltage",
    "DTC_CAN_Timeout",
    "DTC_CAN_Failure",
    "DTC_Sensor_Failure",
    "DTC_NVM_Error",
]


# ------------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------------

def set_vector(hil: HILTest, vector: dict):
    """Setzt den Eingangsvektor: iteriert per for-Schleife ueber {Signalname: True/False}."""
    for signal_name, is_true in vector.items():
        value = SIGNAL_TRUE_VALUE if is_true else SIGNAL_FALSE_VALUE
        hil.set_system_variable_value(NS_SIGNAL, signal_name, value)
    time.sleep(SETTLE_TIME)


def verify_flag(hil: HILTest, expected_value: int) -> bool:
    """Prueft ob Flag den erwarteten Boolean-Wert hat."""
    return hil.verify_system_variable_with_tolerance(
        NS_FLAG, VAR_FLAG, expected_value, tolerance=0
    )


def run_test_case(hil: HILTest, test_id: str, vector: list, expected_flag: int, description: str):
    """Fuehrt einen einzelnen MC/DC-Testfall aus: Vektor setzen, Flag verifizieren."""
    hil.start_test_case(f"{test_id}_{description}")

    if not hil.check_precondition_operation_mode(DTC_Signals):
        return

    set_vector(hil, vector)
    verify_flag(hil, expected_flag)


# ------------------------------------------------------------------
# Hauptprogramm — alle MC/DC-Testfaelle per for-Schleife ausfuehren
# ------------------------------------------------------------------

def main():
    hil = HILTest(CANOE_CONFIG)

    try:
        for test_id, vector, expected_flag, description in TEST_CASES:
            run_test_case(hil, test_id, vector, expected_flag, description)

    finally:
        hil.save_report(REPORT_PATH)
        hil.close()
        print(f"Report gespeichert: {REPORT_PATH}")


if __name__ == "__main__":
    main()
