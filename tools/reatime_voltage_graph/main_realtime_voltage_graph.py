import sys
import threading
import numpy as np
import time
from collections import deque
from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import adafruit_ads1x15.ads1115 as ADS1115_module
import adafruit_ads1x15.ads1015 as ADS1015_module
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio
from pyqtgraph import LegendItem
from PyQt6.QtWidgets import QGraphicsProxyWidget, QGraphicsWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Constants
SUPPORTED_BOARDS = ['ADS1015', 'ADS1115']
POSSIBLE_ADDRESSES = [0x48, 0x49, 0x4A, 0x4B]
ADS1X15_DATA_RATES = {
    'ADS1115': [8, 16, 32, 64, 128, 250, 475, 860],
    'ADS1015': [128, 250, 490, 920, 1600, 2400, 3300]
}
CHANNEL_COLORS = ['r', 'g', 'b', 'c']
MAX_ERRORS = 10
DEFAULTS = {
    'board': 'ADS1115',
    'data_rate': 128,
    'address': 0x4A,
    'plot_length': 10,
    'plot_every': 500,
    'rolling_window': 1000
}

class CustomLegendItem(LegendItem):
    def __init__(self, size=None, offset=None):
        super().__init__(size, offset)
        self.layout.setSpacing(1)

class SetupDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Board selection
        self.board_label = QtWidgets.QLabel("Select Board:")
        self.board_combo = QtWidgets.QComboBox()
        self.board_combo.addItems(SUPPORTED_BOARDS)
        self.board_combo.setCurrentText(DEFAULTS['board'])
        self.board_combo.currentTextChanged.connect(self.update_data_rates)

        # Data rate selection
        self.data_rate_label = QtWidgets.QLabel("Select Data Rate:")
        self.data_rate_combo = QtWidgets.QComboBox()
        self.update_data_rates(DEFAULTS['board'])
        self.data_rate_combo.setCurrentText(str(DEFAULTS['data_rate']))

        # Address selection
        self.address_label = QtWidgets.QLabel("Select I2C Address:")
        self.address_combo = QtWidgets.QComboBox()
        addresses = [hex(addr) for addr in POSSIBLE_ADDRESSES]
        self.address_combo.addItems(addresses)
        self.address_combo.setCurrentText(hex(DEFAULTS['address']))

        # Test button and result
        self.test_button = QtWidgets.QPushButton("Test Settings")
        self.test_button.clicked.connect(self.test_settings)
        self.test_result = QtWidgets.QLabel("")

        # Plot Length slider
        self.plot_length_label = QtWidgets.QLabel(f"Plot Length: {DEFAULTS['plot_length']} s")
        self.plot_length_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.plot_length_slider.setRange(4, 1200)
        self.plot_length_slider.setValue(DEFAULTS['plot_length'])
        self.plot_length_slider.valueChanged.connect(self.update_plot_length_label)

        # Plot Every slider
        self.plot_every_label = QtWidgets.QLabel(f"Plot Every: {DEFAULTS['plot_every']} ms")
        self.plot_every_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.plot_every_slider.setRange(100, 1000)
        self.plot_every_slider.setValue(DEFAULTS['plot_every'])
        self.plot_every_slider.valueChanged.connect(self.update_plot_every_label)

        # Rolling Window slider
        self.rolling_window_label = QtWidgets.QLabel(f"Rolling Window: {DEFAULTS['rolling_window']} ms")
        self.rolling_window_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.rolling_window_slider.setRange(100, 2000)
        self.rolling_window_slider.setValue(DEFAULTS['rolling_window'])
        self.rolling_window_slider.valueChanged.connect(self.update_rolling_window_label)

        # Start button
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_main_window)

        # Layout arrangement
        layout.addWidget(self.board_label)
        layout.addWidget(self.board_combo)
        layout.addWidget(self.data_rate_label)
        layout.addWidget(self.data_rate_combo)
        layout.addWidget(self.address_label)
        layout.addWidget(self.address_combo)
        layout.addWidget(self.test_button)
        layout.addWidget(self.test_result)
        layout.addWidget(self.plot_length_label)
        layout.addWidget(self.plot_length_slider)
        layout.addWidget(self.plot_every_label)
        layout.addWidget(self.plot_every_slider)
        layout.addWidget(self.rolling_window_label)
        layout.addWidget(self.rolling_window_slider)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def update_data_rates(self, board):
        self.data_rate_combo.clear()
        rates = [str(rate) for rate in ADS1X15_DATA_RATES[board]]
        self.data_rate_combo.addItems(rates)

    def update_plot_length_label(self, value):
        self.plot_length_label.setText(f"Plot Length: {value} s")

    def update_plot_every_label(self, value):
        self.plot_every_label.setText(f"Plot Every: {value} ms")

    def update_rolling_window_label(self, value):
        self.rolling_window_label.setText(f"Rolling Window: {value} ms")

    def test_settings(self):
        board_type = self.board_combo.currentText()
        address = int(self.address_combo.currentText(), 16)
        data_rate = int(self.data_rate_combo.currentText())

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            if board_type == 'ADS1115':
                adc = ADS1115_module.ADS1115(i2c, address=address)
            else:
                adc = ADS1015_module.ADS1015(i2c, address=address)
            adc.data_rate = data_rate
            channel = AnalogIn(adc, ADS1115_module.P0)
            reading = channel.value
            self.test_result.setText(f"Reading: {reading}")
        except Exception as e:
            self.test_result.setText("FAILED")
            print(f"Test failed: {e}")

    def start_main_window(self):
        settings = {
            'board': self.board_combo.currentText(),
            'data_rate': int(self.data_rate_combo.currentText()),
            'address': int(self.address_combo.currentText(), 16),
            'plot_length': self.plot_length_slider.value(),
            'plot_every': self.plot_every_slider.value(),
            'rolling_window': self.rolling_window_slider.value()
        }
        self.main_window = PlotWindow(settings)
        self.main_window.show()
        self.close()

class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.init_ui()
        self.init_adc()
        self.init_data()
        self.init_threads()
        self.error_count = 0

    def init_ui(self):
        self.setWindowTitle("Real-Time Voltage Graph")
        self.resize(1920, 1080)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Voltage', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='s')

        # Custom legend
        self.legend = CustomLegendItem((100,60), offset=(70,30))
        self.legend.setParentItem(self.plot_widget.graphicsItem())
        self.checkboxes = []
        self.std_labels = []

        # Layout arrangement
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.plot_widget)

        # Add Reset Y-Axis button
        self.reset_y_button = QtWidgets.QPushButton("Reset Y-Axis")
        self.reset_y_button.clicked.connect(self.reset_y_axis)
        layout.addWidget(self.reset_y_button)

        self.central_widget.setLayout(layout)

        # Close event
        self.close_event = threading.Event()

    def init_adc(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            if self.settings['board'] == 'ADS1115':
                self.adc = ADS1115_module.ADS1115(i2c, address=self.settings['address'])
            else:
                self.adc = ADS1015_module.ADS1015(i2c, address=self.settings['address'])
            self.adc.data_rate = self.settings['data_rate']
            self.channels = [AnalogIn(self.adc, getattr(ADS1115_module, f'P{i}')) for i in range(4)]
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "ADC Initialization Error", str(e))
            sys.exit(1)

    def init_data(self):
        self.plot_length = self.settings['plot_length']
        self.plot_every = self.settings['plot_every']
        self.rolling_window = self.settings['rolling_window']
        self.sample_size = int((self.rolling_window * self.settings['data_rate']) / 1000)

        self.time_buffer = deque(maxlen=self.plot_length * self.settings['data_rate'])
        self.data_buffers = [deque(maxlen=self.plot_length * self.settings['data_rate']) for _ in range(4)]
        self.curves = []
        for i in range(4):
            curve = self.plot_widget.plot(pen=CHANNEL_COLORS[i], name=f"Channel {i}")
            self.curves.append(curve)

            checkbox = QtWidgets.QCheckBox(f"Channel {i}")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_plot_visibility)
            self.checkboxes.append(checkbox)

            std_label = QtWidgets.QLabel(f"Std Dev: 0")
            self.std_labels.append(std_label)

            legend_widget = QtWidgets.QWidget()
            legend_layout = QtWidgets.QHBoxLayout(legend_widget)
            legend_layout.addWidget(checkbox)
            legend_layout.addWidget(std_label)
            legend_layout.setContentsMargins(0, 0, 0, 0)
            legend_widget.setLayout(legend_layout)
            
            proxy_widget = QGraphicsProxyWidget()
            proxy_widget.setWidget(legend_widget)
            
            # Create a color sample
            color_sample = pg.PlotDataItem(pen=CHANNEL_COLORS[i])
            
            # Add both the color sample and our custom widget to the legend
            self.legend.addItem(color_sample, '')
            self.legend.layout.addItem(proxy_widget, i, 1)

        # Initialize Y-axis range
        initial_values = [channel.voltage for channel in self.channels]
        min_voltage = min(initial_values) * 0.9
        max_voltage = max(initial_values) * 1.1
        self.plot_widget.setYRange(min_voltage, max_voltage)

    def init_threads(self):
        self.data_thread = threading.Thread(target=self.collect_data)
        self.data_thread.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.plot_every)

    def collect_data(self):
        start_time = time.time()
        while not self.close_event.is_set():
            try:
                current_time = time.time() - start_time
                voltages = [channel.voltage for channel in self.channels]
                
                self.time_buffer.append(current_time)
                for i, voltage in enumerate(voltages):
                    self.data_buffers[i].append(voltage)
                
                self.error_count = 0
            except Exception as e:
                self.error_count += 1
                if self.error_count > MAX_ERRORS:
                    self.close_event.set()
                    QtWidgets.QMessageBox.critical(self, "Data Collection Error",
                                                   f"Failed to read data from address {hex(self.settings['address'])}")
                    QtCore.QCoreApplication.quit()
                else:
                    # Use last values if error occurs
                    if self.data_buffers[0]:
                        for i in range(4):
                            self.data_buffers[i].append(self.data_buffers[i][-1])
                    else:
                        for i in range(4):
                            self.data_buffers[i].append(0)
            time.sleep(1 / self.settings['data_rate'])

    def update_plot(self):
        min_voltage = float('inf')
        max_voltage = float('-inf')
        
        for i, curve in enumerate(self.curves):
            if self.checkboxes[i].isChecked():
                times = list(self.time_buffer)
                voltages = list(self.data_buffers[i])
                
                # Ensure times and voltages have the same length
                min_length = min(len(times), len(voltages))
                times = times[-min_length:]
                voltages = voltages[-min_length:]
                
                curve.setData(times, voltages)
                if len(voltages) >= self.sample_size:
                    window_data = voltages[-self.sample_size:]
                    std_dev = np.std(window_data)
                    self.std_labels[i].setText(f"Std Dev: {std_dev:.4f}")
                    
                    # Update min and max voltage for visible data
                    min_voltage = min(min_voltage, min(window_data))
                    max_voltage = max(max_voltage, max(window_data))
                else:
                    self.std_labels[i].setText("Std Dev: N/A")
                curve.show()
            else:
                curve.hide()
        
        if self.time_buffer:
            current_time = max(self.time_buffer)
            self.plot_widget.setXRange(current_time - self.plot_length, current_time)
            
            # Update y-axis range with some padding
            if min_voltage != float('inf') and max_voltage != float('-inf'):
                voltage_range = max_voltage - min_voltage
                padding = voltage_range * 0.1  # 10% padding
                self.plot_widget.setYRange(min_voltage - padding, max_voltage + padding)

    def update_plot_visibility(self):
        self.update_plot()  # This will handle showing/hiding curves based on checkbox states

    def closeEvent(self, event):
        self.close_event.set()
        self.data_thread.join()
        event.accept()

    def reset_y_axis(self):
        all_voltages = [v for buffer in self.data_buffers for v in buffer]
        if all_voltages:
            min_v = min(all_voltages)
            max_v = max(all_voltages)
            range_v = max_v - min_v
            self.plot_widget.setYRange(min_v - range_v * 0.1, max_v + range_v * 0.1)

def main():
    app = QtWidgets.QApplication(sys.argv)
    setup_dialog = SetupDialog()
    setup_dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()