"""
Test: ADC Auflösung & Formel-Verifikation (12-Bit)
====================================================
Ziel: Prüfen ob die ADC-Formel stimmt:
      ADC_erwartet = (Spannung / 5.0) * 4095

      Für jede Spannung in Voltage_Values wird der gemessene ADC-Wert
      mit dem berechneten Sollwert verglichen. Ergebnis erscheint im Report.
"""

import time
from HIL_Test import HILTest

# ------------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------------
CANOE_CONFIG  = "file"
REPORT_PATH   = "C:/Reports/ADC_report.txt"

NS_VOLTAGE    = "Voltage"               # Namespace der Eingangs-Spannung
VAR_VOLTAGE   = "Voltage"              # Systemvariable für Spannung [V]
NS_ADC        = "ADC"                   # Namespace des ADC-Ausgangs
VAR_ADC       = "ADC_Value"             # Systemvariable für ADC-Wert [0…4095]

ADC_MAX       = 4095                    # 12-Bit ADC Maximum (2^12 - 1)
VOLTAGE_MAX   = 5.0                     # Referenzspannung [V]
TOLERANCE_LSB = 2                       # Erlaubte Abweichung ± 2 ADC-Counts
SETTLE_TIME   = 0.1                     # Wartezeit nach Spannungsänderung [s]

# Testspannungen (dürfen ungeordnet sein — jede wird einzeln geprüft)
VOLTAGE_VALUES = [0.0, 1.9, 2.3, 5.0]

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
# TC_1 — ADC-Formel für alle Testspannungen prüfen
# ------------------------------------------------------------------

def TC_1():
    """
    Ziel: Für jede Spannung in VOLTAGE_VALUES wird geprüft ob der
          gemessene ADC-Wert der linearen Formel entspricht.
          Ergebnis (PASS/FAIL) wird automatisch in den Report geschrieben.
    """
    HIL.start_test_case("TC_1_ADC_Formel_Verifikation_12Bit")

    # Precondition: kein DTC aktiv, ECU im Normalbetrieb
    if not HIL.check_precondition_operation_mode(DTC_Signals):
        return

    for voltage in VOLTAGE_VALUES:
        # Eingangsspannung setzen
        HIL.set_system_variable_value(NS_VOLTAGE, VAR_VOLTAGE, voltage)

        # Warten bis ADC den neuen Wert verarbeitet hat
        time.sleep(SETTLE_TIME)

        # ADC-Wert lesen und mit Sollwert vergleichen → geht automatisch in Report
        HIL.verify_adc_value(
            voltage_input=voltage,
            namespace=NS_ADC,
            variable=VAR_ADC,
            tolerance=TOLERANCE_LSB,
            adc_max=ADC_MAX,
            voltage_max=VOLTAGE_MAX,
        )

    # Spannung nach Test auf 0 V zurücksetzen
    HIL.set_system_variable_value(NS_VOLTAGE, VAR_VOLTAGE, 0.0)


# ------------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------------

try:
    TC_1()

finally:
    HIL.save_report(REPORT_PATH)
    HIL.close()
    print(f"Report gespeichert: {REPORT_PATH}")
