# tools/realtime_voltage_graph/main_rtvg.py

import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox,
                             QPushButton, QLineEdit, QSlider, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import QTimer, Qt
import pyqtgraph as pg
import numpy as np
from loguru import logger
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

ADS1X15_DATA_RATES = {
    'ADS1115': [8, 16, 32, 64, 128, 250, 475, 860],
    'ADS1015': [128, 250, 490, 920, 1600, 2400, 3300]
}

CHANNEL_COLORS = ['r', 'g', 'b', 'c']

class SetupDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle('Voltage Graph Setup')

        self.address_input = QLineEdit('4a')
        self.layout.addWidget(QLabel('I2C Address (hex):'))
        self.layout.addWidget(self.address_input)

        self.board_type = QComboBox()
        self.board_type.addItems(['ADS1115', 'ADS1015'])
        self.layout.addWidget(QLabel('Board Type:'))
        self.layout.addWidget(self.board_type)

        self.data_rate = QComboBox()
        self.layout.addWidget(QLabel('Data Rate:'))
        self.layout.addWidget(self.data_rate)
        self.board_type.currentTextChanged.connect(self.update_data_rates)

        self.pin_selection = QComboBox()
        self.pin_selection.addItems(['All', 'Pin 0', 'Pin 1', 'Pin 2', 'Pin 3'])
        self.layout.addWidget(QLabel('Pin Selection:'))
        self.layout.addWidget(self.pin_selection)

        self.test_button = QPushButton('Test Board')
        self.layout.addWidget(self.test_button)

        self.plot_length = QSlider(Qt.Orientation.Horizontal)
        self.plot_length.setRange(5, 120)
        self.plot_length.setValue(20)
        self.plot_length_label = QLabel('Plot Length: 20 seconds')
        self.layout.addWidget(self.plot_length_label)
        self.layout.addWidget(self.plot_length)
        self.plot_length.valueChanged.connect(self.update_plot_length_label)

        self.margin = QSlider(Qt.Orientation.Horizontal)
        self.margin.setRange(0, 100)
        self.margin.setValue(10)
        self.margin_label = QLabel('Y-axis Margin: 10%')
        self.layout.addWidget(self.margin_label)
        self.layout.addWidget(self.margin)
        self.margin.valueChanged.connect(self.update_margin_label)

        self.start_button = QPushButton('Start')
        self.layout.addWidget(self.start_button)

        self.update_data_rates()

    def update_data_rates(self):
        self.data_rate.clear()
        self.data_rate.addItems(map(str, ADS1X15_DATA_RATES[self.board_type.currentText()]))
        self.data_rate.setCurrentText('128')  # Set default to 128 SPS

    def update_plot_length_label(self, value):
        self.plot_length_label.setText(f'Plot Length: {value} seconds')

    def update_margin_label(self, value):
        self.margin_label.setText(f'Y-axis Margin: {value}%')

class RealtimeVoltageGraph(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle('Realtime Voltage Graph')
        self.setGeometry(0, 0, 1920, 1080)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.setup_plot()
        self.setup_ads1115()
        self.setup_data_collection()

    def setup_plot(self):
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Voltage', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True)

        self.curves = []
        for color in CHANNEL_COLORS:
            curve = self.plot_widget.plot(pen=pg.mkPen(color, width=2, alpha=128))
            self.curves.append(curve)

        self.data = [[] for _ in range(4)]
        self.times = []

    def setup_ads1115(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(i2c, address=int(self.config['address'], 16))
            self.ads.data_rate = 128  # Fixed at 128 SPS
            self.channels = [AnalogIn(self.ads, getattr(ADS, f'P{i}')) for i in range(4)]
            logger.info(f"ADS1115 initialized with address: {self.config['address']}")
        except Exception as e:
            logger.error(f"Error initializing ADS1115: {e}")
            raise

    def setup_data_collection(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)  # Update every second
        self.start_time = time.perf_counter()
        self.last_update_time = self.start_time

    def update_plot(self):
        current_time = time.perf_counter()
        elapsed_time = current_time - self.start_time
        time_since_last_update = current_time - self.last_update_time

        samples_to_collect = int(time_since_last_update * 128)  # 128 SPS

        new_times = np.linspace(self.last_update_time - self.start_time, elapsed_time, samples_to_collect)
        self.times.extend(new_times)

        for i, channel in enumerate(self.channels):
            try:
                new_data = [channel.voltage for _ in range(samples_to_collect)]
                self.data[i].extend(new_data)
            except Exception as e:
                logger.warning(f"Error reading channel {i}: {e}")
                self.data[i].extend([self.data[i][-1] if self.data[i] else 0] * samples_to_collect)

        # Limit data points based on plot length
        max_data_points = 128 * int(self.config['plot_length'])
        if len(self.times) > max_data_points:
            self.times = self.times[-max_data_points:]
            for i in range(len(self.data)):
                self.data[i] = self.data[i][-max_data_points:]

        self.update_y_range()

        pin_selection = self.config['pin_selection']
        if pin_selection == 'All':
            for i, curve in enumerate(self.curves):
                curve.setData(self.times, self.data[i])
                curve.show()
            print(f"Last values - A0: {self.data[0][-1]:.6f}V, A1: {self.data[1][-1]:.6f}V, A2: {self.data[2][-1]:.6f}V, A3: {self.data[3][-1]:.6f}V")
        else:
            pin = int(pin_selection.split()[-1])
            for i, curve in enumerate(self.curves):
                if i == pin:
                    curve.setData(self.times, self.data[i])
                    curve.show()
                    print(f"Last value - A{pin}: {self.data[pin][-1]:.6f}V")
                else:
                    curve.hide()

        self.plot_widget.setXRange(max(0, elapsed_time - int(self.config['plot_length'])), elapsed_time)
        self.last_update_time = current_time

    def update_y_range(self):
        if not any(self.data):
            return

        min_val = min(min(channel) for channel in self.data if channel)
        max_val = max(max(channel) for channel in self.data if channel)
        
        if min_val == max_val:
            min_val -= 0.1
            max_val += 0.1
        
        range_val = max_val - min_val
        margin = range_val * (int(self.config['margin']) / 100)

        self.plot_widget.setYRange(min_val - margin, max_val + margin)

        # Update y-axis tick formatting
        y_axis = self.plot_widget.getAxis('left')
        y_axis.setTickSpacing(major=range_val / 5, minor=range_val / 25)
        y_axis.setStyle(tickTextOffset=5)
        
        # Set label format to show more decimal places
        y_axis.setLabel(format='{value:.8f}')

        logger.debug(f"Y-axis range updated: {min_val - margin:.6f} to {max_val + margin:.6f}")

def test_board(address, board_type):
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        ads_class = ADS.ADS1115 if board_type == 'ADS1115' else ADS.ADS1015
        ads = ads_class(i2c, address=int(address, 16))
        channels = [AnalogIn(ads, getattr(ADS, f'P{i}')) for i in range(4)]
        readings = [channel.voltage for channel in channels]
        return f"Success! Readings: {readings}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    app = QApplication(sys.argv)
    setup_dialog = SetupDialog()

    def on_test():
        result = test_board(setup_dialog.address_input.text(), setup_dialog.board_type.currentText())
        QMessageBox.information(setup_dialog, "Board Test Result", result)

    setup_dialog.test_button.clicked.connect(on_test)

    main_window = None  # This will hold our main window

    def on_start():
        nonlocal main_window
        config = {
            'address': setup_dialog.address_input.text(),
            'board_type': setup_dialog.board_type.currentText(),
            'data_rate': setup_dialog.data_rate.currentText(),
            'plot_length': setup_dialog.plot_length.value(),
            'margin': setup_dialog.margin.value(),
            'pin_selection': setup_dialog.pin_selection.currentText()
        }
        setup_dialog.close()
        main_window = RealtimeVoltageGraph(config)
        main_window.show()

    setup_dialog.start_button.clicked.connect(on_start)
    setup_dialog.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()