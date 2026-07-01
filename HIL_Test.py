from py_canoe import CANoe
import time
import datetime


class HILTest:
    """
    HIL (Hardware-In-the-Loop) Test Framework für CANoe-basierte Fahrzeugtests.

    Kapselt die py_canoe-API und stellt Test-Hilfsfunktionen bereit:
    - Signal- und Systemvariablen-Lese/-Schreibzugriff
    - Environment Variable Zugriff
    - Polling mit Timeout (wait_for_*)
    - Statistik-Erfassung (collect_system_variable_values)
    - Toleranzbasierte Verifikation (verify_*_with_tolerance)
    - ADC-Verifikation mit Interpolation (verify_adc_value)
    - 1D-Interpolation (interpolate)
    - Semiautomatic-Step für manuelle Eingriffe (wait_for_test_completion)
    - Testreport-Generierung (start_test_case, save_report)
    """

    def __init__(self, config_path: str):
        """
        Öffnet die CANoe-Konfiguration und startet die Messung.

        :param config_path: Absoluter Pfad zur .cfg-Datei von CANoe.
        """
        self.config_path = config_path
        self.canoe = CANoe()
        self.canoe.open(self.config_path)
        self.canoe.start_measurement()

        # Report-Zustand
        self._report_lines: list = []
        self._test_case_name: str = ''
        self._pass_count: int = 0
        self._fail_count: int = 0
        self._tc_start_time: datetime.datetime = None

    def close(self):
        """
        Stoppt die CANoe-Messung und schließt die Verbindung sauber.

        Sollte am Ende jedes Tests aufgerufen werden, um Ressourcen freizugeben.
        """
        self.canoe.stop_measurement()
        self.canoe.quit()

    # ------------------------------------------------------------------
    # Report-System
    # ------------------------------------------------------------------

    def start_test_case(self, name: str):
        """
        Startet einen neuen Testfall im Report.

        Jeder Aufruf von start_test_case beginnt einen neuen Abschnitt im Report.
        Pass/Fail-Zähler werden zurückgesetzt.

        :param name: Name des Testfalls (z. B. 'TC_001_ADC_Test').
        """
        self._test_case_name = name
        self._pass_count = 0
        self._fail_count = 0
        self._tc_start_time = datetime.datetime.now()

        self._report_lines.append('')
        self._report_lines.append(f'TEST CASE: {name}')
        self._report_lines.append(f'Start: {self._tc_start_time.strftime("%H:%M:%S.%f")[:-3]}')
        self._report_lines.append('-' * 72)

    def _log(self, action: str, details: str, result: str = 'INFO'):
        """
        Schreibt einen Eintrag in den internen Report-Puffer.

        :param action:  Kürzel der Aktion (z. B. 'SET Signal', 'VERIFY SysVar').
        :param details: Beschreibung mit Werten.
        :param result:  'INFO', 'PASS' oder 'FAIL'.
        """
        timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        line = f'[{timestamp}] [{result:<4}]  {action:<16} | {details}'
        self._report_lines.append(line)

        if result == 'PASS':
            self._pass_count += 1
        elif result == 'FAIL':
            self._fail_count += 1

    def _close_test_case(self):
        """Schreibt die Zusammenfassung des aktuellen Testfalls in den Puffer."""
        if not self._test_case_name:
            return
        end_time = datetime.datetime.now()
        overall = 'PASS' if self._fail_count == 0 else 'FAIL'
        self._report_lines.append(f'End:    {end_time.strftime("%H:%M:%S.%f")[:-3]}')
        self._report_lines.append(
            f'Result: {overall}  ({self._pass_count} passed, {self._fail_count} failed)'
        )
        self._report_lines.append('=' * 72)

    def save_report(self, file_path: str):
        """
        Schließt den letzten Testfall und speichert den Report als .txt-Datei.

        :param file_path: Ausgabepfad z. B. 'C:/Reports/report.txt'.
        """
        self._close_test_case()

        header = [
            '=' * 72,
            'TEST REPORT  —  HIL Test Framework',
            f'Generated : {datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")}',
            f'Config    : {self.config_path}',
            '=' * 72,
        ]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header + self._report_lines) + '\n')

    # ------------------------------------------------------------------
    # Grundlegende Signal- und Systemvariablen-Zugriffe
    # ------------------------------------------------------------------

    def set_signal_value(self, channel: str, message: str, signal: str, value):
        """Setzt den Wert eines CAN-Signals in CANoe."""
        self.canoe.set_signal_value(channel, message, signal, value)
        self._log('SET Signal', f'{channel} :: {message} :: {signal} = {value}')

    def get_signal_value(self, channel: str, message: str, signal: str):
        """Liest den aktuellen Wert eines CAN-Signals aus CANoe."""
        value = self.canoe.get_signal_value(channel, message, signal)
        self._log('GET Signal', f'{channel} :: {message} :: {signal} → {value}')
        return value

    def get_system_variable_value(self, namespace: str, variable: str):
        """Liest den aktuellen Wert einer CANoe-Systemvariable."""
        return self.canoe.get_system_variable_value(namespace, variable)

    def set_system_variable_value(self, namespace: str, variable: str, value):
        """Setzt den Wert einer CANoe-Systemvariable."""
        self.canoe.set_system_variable_value(namespace, variable, value)
        self._log('SET SysVar', f'{namespace}::{variable} = {value}')

    def get_environment_variable_value(self, variable: str):
        """
        Liest den aktuellen Wert einer CANoe-Umgebungsvariable (Environment Variable).

        Unterschied zu Systemvariablen: Umgebungsvariablen haben keinen Namespace,
        sie werden direkt über ihren Namen angesprochen.

        :param variable: Name der Umgebungsvariable (z. B. 'IgnitionState').
        :return:         Aktueller Wert der Umgebungsvariable.
        """
        value = self.canoe.get_environment_variable_value(variable)
        self._log('GET EnvVar', f'{variable} → {value}')
        return value

    def set_environment_variable_value(self, variable: str, value):
        """
        Setzt den Wert einer CANoe-Umgebungsvariable (Environment Variable).

        :param variable: Name der Umgebungsvariable (z. B. 'IgnitionState').
        :param value:    Neuer Wert (Integer, Float oder String je nach Typ).
        """
        self.canoe.set_environment_variable_value(variable, value)
        self._log('SET EnvVar', f'{variable} = {value}')

    # ------------------------------------------------------------------
    # Polling-Funktionen mit Timeout
    # ------------------------------------------------------------------

    def wait_for_system_variable(
        self, namespace: str, variable: str, expected_value, timeout: float
    ) -> bool:
        """
        Wartet bis eine Systemvariable den erwarteten Wert annimmt.

        Polling-Intervall: 100 ms.

        :param namespace:      CANoe-Namespace der Systemvariable.
        :param variable:       Name der Systemvariable.
        :param expected_value: Zielwert, auf den gewartet wird.
        :param timeout:        Maximale Wartezeit in Sekunden.
        :return:               True  → Zielwert innerhalb timeout erreicht.
                               False → Timeout abgelaufen.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_value = self.get_system_variable_value(namespace, variable)
            if current_value == expected_value:
                self._log(
                    'WAIT SysVar',
                    f'{namespace}::{variable} == {expected_value}  (timeout: {timeout}s)',
                    result='PASS',
                )
                return True
            time.sleep(0.1)

        self._log(
            'WAIT SysVar',
            f'{namespace}::{variable} == {expected_value}  (timeout: {timeout}s)  → TIMEOUT',
            result='FAIL',
        )
        return False

    def wait_for_signal(
        self,
        channel: str,
        message: str,
        signal: str,
        expected_value,
        timeout: float,
    ) -> bool:
        """
        Wartet bis ein CAN-Signal den erwarteten Wert annimmt.

        Polling-Intervall: 100 ms.

        :param channel:        CAN-Kanal (z. B. 'CAN 1').
        :param message:        CAN-Nachrichtenname.
        :param signal:         Signalname innerhalb der Nachricht.
        :param expected_value: Zielwert, auf den gewartet wird.
        :param timeout:        Maximale Wartezeit in Sekunden.
        :return:               True  → Zielwert innerhalb timeout erreicht.
                               False → Timeout abgelaufen.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_value = self.get_signal_value(channel, message, signal)
            if current_value == expected_value:
                self._log(
                    'WAIT Signal',
                    f'{channel}::{message}::{signal} == {expected_value}  (timeout: {timeout}s)',
                    result='PASS',
                )
                return True
            time.sleep(0.1)

        self._log(
            'WAIT Signal',
            f'{channel}::{message}::{signal} == {expected_value}  (timeout: {timeout}s)  → TIMEOUT',
            result='FAIL',
        )
        return False

    # ------------------------------------------------------------------
    # Statistik-Erfassung
    # ------------------------------------------------------------------

    def collect_system_variable_values(
        self, namespace: str, variable: str, sample_count: int = 20
    ) -> tuple:
        """
        Sammelt mehrere Messwerte einer Systemvariable und berechnet Statistiken.

        Sampling-Intervall: 50 ms; maximale Erfassungszeit: 2 s.

        :param namespace:    CANoe-Namespace der Systemvariable.
        :param variable:     Name der Systemvariable.
        :param sample_count: Anzahl der zu erfassenden Samples (Standard: 20).
        :return:             Tuple (average, max, min). Bei leerer Sample-Liste (0, 0, 0).
        """
        values = []
        start_time = time.time()
        while len(values) < sample_count and (time.time() - start_time) < 2.0:
            current_value = self.get_system_variable_value(namespace, variable)
            values.append(current_value)
            time.sleep(0.05)

        if not values:
            return (0.0, 0.0, 0.0)

        avg = sum(values) / len(values)
        result = (avg, max(values), min(values))
        self._log(
            'COLLECT SysVar',
            f'{namespace}::{variable}  avg={avg:.3f}  max={result[1]}  min={result[2]}  n={len(values)}',
        )
        return result

    # ------------------------------------------------------------------
    # Toleranzbasierte Verifikation
    # ------------------------------------------------------------------

    def verify_system_variable_with_tolerance(
        self, namespace: str, variable: str, expected_value, tolerance: float
    ) -> bool:
        """
        Prüft ob eine Systemvariable innerhalb von expected ± tolerance liegt.

        :return: True wenn |current − expected| ≤ tolerance.
        """
        current_value = self.get_system_variable_value(namespace, variable)
        passed = abs(current_value - expected_value) <= tolerance
        self._log(
            'VERIFY SysVar',
            f'{namespace}::{variable}  expected={expected_value} ±{tolerance}  actual={current_value}',
            result='PASS' if passed else 'FAIL',
        )
        return passed

    def verify_signal_with_tolerance(
        self,
        channel: str,
        message: str,
        signal: str,
        expected_value,
        tolerance: float,
    ) -> bool:
        """
        Prüft ob ein CAN-Signal innerhalb von expected ± tolerance liegt.

        :return: True wenn |current − expected| ≤ tolerance.
        """
        current_value = self.get_signal_value(channel, message, signal)
        passed = abs(current_value - expected_value) <= tolerance
        self._log(
            'VERIFY Signal',
            f'{channel}::{message}::{signal}  expected={expected_value} ±{tolerance}  actual={current_value}',
            result='PASS' if passed else 'FAIL',
        )
        return passed

    # ------------------------------------------------------------------
    # Semiautomatic-Step
    # ------------------------------------------------------------------

    def wait_for_test_completion(
        self, prompt: str = "Is the test completed? (yes/no): "
    ) -> bool:
        """
        Hält den Testablauf an und wartet auf manuelle Bestätigung des Testers.

        Nützlich für Schritte, die physische Eingriffe erfordern
        (z. B. Stecker ziehen, Taste drücken).

        :param prompt: Anzeigetext für die Konsoleneingabe.
        :return:       True sobald der Tester 'yes' oder 'y' eingibt.
        """
        self._log('MANUAL STEP', prompt)
        while True:
            user_input = input(prompt).strip().lower()
            if user_input in ['yes', 'y']:
                self._log('MANUAL STEP', 'Tester confirmed → OK', result='PASS')
                return True
            elif user_input in ['no', 'n']:
                print("Waiting for test completion...")
                time.sleep(1.0)
            else:
                print("Please answer 'yes' or 'no'.")

    # ------------------------------------------------------------------
    # 1D-Interpolation
    # ------------------------------------------------------------------

    @staticmethod
    def interpolate(x_table: list, y_table: list, x_input: float) -> float:
        """
        Lineare 1D-Interpolation auf einer sortierten Lookup-Table.

        Außerhalb des Definitionsbereichs wird auf den jeweiligen Randwert
        geklemmt (Clamp-Verhalten wie in typischen ECU-Implementierungen).

        Beispiel::

            x_table = [0, 10, 20, 30]
            y_table = [0, 100, 180, 250]
            interpolate(x_table, y_table, 15)  # → 140.0

        :param x_table:  Aufsteigend sortierte Eingangsstützstellen (Breakpoints).
        :param y_table:  Zugehörige Ausgangswerte (gleiche Länge wie x_table).
        :param x_input:  Eingangswert, für den der Ausgangswert berechnet werden soll.
        :return:         Interpolierter Ausgangswert.
        :raises ValueError: Wenn Tabellen unterschiedlich lang oder kürzer als 2 sind.
        """
        if len(x_table) != len(y_table):
            raise ValueError("x_table and y_table must have the same length.")
        if len(x_table) < 2:
            raise ValueError("Tables must contain at least 2 breakpoints.")

        if x_input <= x_table[0]:
            return float(y_table[0])

        if x_input >= x_table[-1]:
            return float(y_table[-1])

        for i in range(len(x_table) - 1):
            if x_table[i] <= x_input <= x_table[i + 1]:
                dx = x_table[i + 1] - x_table[i]
                t = (x_input - x_table[i]) / dx
                return y_table[i] + t * (y_table[i + 1] - y_table[i])

        return float(y_table[-1])

    # ------------------------------------------------------------------
    # ADC-Verifikation
    # ------------------------------------------------------------------

    def verify_adc_value(
        self,
        voltage_input: float,
        namespace: str,
        variable: str,
        tolerance: float,
        adc_max: int = 4095,
        voltage_max: float = 5.0,
        calibration_volts: list = None,
        calibration_adc: list = None,
    ) -> dict:
        """
        Verifiziert den ADC-Wert einer Systemvariable für eine gegebene Eingangsspannung.

        Zwei Modi:
          1. Linear (Standard): erwartet = (voltage_input / voltage_max) * adc_max
          2. Kalibriert:        erwartet = interpolate(calibration_volts, calibration_adc, voltage_input)

        :param voltage_input:      Eingangsspannung in Volt.
        :param namespace:          CANoe-Namespace der ADC-Systemvariable.
        :param variable:           Name der ADC-Systemvariable.
        :param tolerance:          Zulässige Abweichung in ADC-Counts.
        :param adc_max:            Maximaler ADC-Wert (Standard: 4095 für 12-bit).
        :param voltage_max:        Maximale Spannung in Volt (Standard: 5.0 V).
        :param calibration_volts:  Spannungs-Stützstellen der Kalibrierungstabelle (optional).
        :param calibration_adc:    ADC-Stützwerte der Kalibrierungstabelle (optional).
        :return:                   Dict mit 'passed', 'voltage', 'expected', 'actual', 'error'.
        """
        if calibration_volts and calibration_adc:
            expected = self.interpolate(calibration_volts, calibration_adc, voltage_input)
            mode = 'calibrated'
        else:
            expected = (voltage_input / voltage_max) * adc_max
            mode = 'linear'

        actual = self.get_system_variable_value(namespace, variable)
        error = abs(actual - expected)
        passed = error <= tolerance

        self._log(
            'VERIFY ADC',
            (f'{namespace}::{variable}  {voltage_input}V → expected={expected:.1f}'
             f'  actual={actual}  error={error:.1f}  tol=±{tolerance}  [{mode}]'),
            result='PASS' if passed else 'FAIL',
        )

        return {
            'passed':   passed,
            'voltage':  voltage_input,
            'expected': expected,
            'actual':   actual,
            'error':    error,
        }
    

    def check_precondition_operation_mode(self, dtc_list: list) -> bool:
        """
        Prüft die Vorbedingungen vor einem Testfall.

        Zwei Bedingungen müssen erfüllt sein:
          1. Operation Mode (Systemvariable STATE::STATE) == 4  (Normalbetrieb)
          2. Alle DTCs aus dtc_list sind inaktiv (Wert == 0)

        :param dtc_list: Liste der DTC-Namen die geprüft werden sollen
                         z. B. ['DTC_Brake_Timeout', 'DTC_Sensor_Fail']
        :return:         True  → System bereit, Test kann starten.
                         False → System nicht bereit (falscher Mode oder aktiver DTC).
        """
        # Aktuellen Operation Mode lesen
        state_mode = self.get_system_variable_value("STATE", "STATE")

        # Alle DTCs aus der Liste prüfen — sammle die aktiven (Wert != 0)
        active_dtcs = [
            dtc for dtc in dtc_list
            if self.get_system_variable_value("DTC", dtc) != 0
        ]

        # Vorbedingung erfüllt wenn Mode == 4 und kein DTC aktiv
        if state_mode == 4 and len(active_dtcs) == 0:
            return True
        else:
            return False
            

                  


