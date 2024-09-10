from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QComboBox, QPushButton, QTextEdit, QProgressBar, 
                             QLabel, QSpinBox, QApplication, QMessageBox)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from voltage_level_collector import DataCollector, save_data
import json
import os

ADS1X15_DATA_RATES = {
    'ADS1115': [8, 16, 32, 64, 128, 250, 475, 860],
    'ADS1015': [128, 250, 490, 920, 1600, 2400, 3300]
}

class VoltageCollectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.apply_dark_theme()

    def load_config(self):
        try:
            config_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'config')
            boards_file = os.path.join(config_dir, 'boards.json')
            devices_file = os.path.join(config_dir, 'devices.json')
            
            with open(boards_file, 'r') as f:
                boards = json.load(f)
            with open(devices_file, 'r') as f:
                devices = json.load(f)
            
            return {'boards': boards, 'devices': devices}
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {'boards': [], 'devices': []}

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.board_selector = QComboBox()
        for board in self.config['boards']:
            if board['type'] in ['ADS1115', 'ADS1015']:
                self.board_selector.addItem(f"{board['label']} ({board['id']})", board['id'])
        self.board_selector.currentIndexChanged.connect(self.update_sample_rates)
        layout.addWidget(QLabel("Select Board:"))
        layout.addWidget(self.board_selector)

        input_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(10)
        input_layout.addWidget(QLabel("Duration (minutes):"))
        input_layout.addWidget(self.duration_spin)

        self.sample_rate_combo = QComboBox()
        input_layout.addWidget(QLabel("Sample Rate (Hz):"))
        input_layout.addWidget(self.sample_rate_combo)
        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Collection")
        self.start_button.clicked.connect(self.start_collection)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Collection")
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        status_layout = QHBoxLayout()
        self.error_count_label = QLabel("Errors: 0")
        status_layout.addWidget(self.error_count_label)
        status_layout.addStretch(1)
        self.quality_label = QLabel("Quality: 100% : 100% : 100% : 100%")
        self.quality_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.quality_label)
        layout.addLayout(status_layout)

        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        layout.addWidget(QLabel("Loaded Configuration:"))
        layout.addWidget(self.config_display)

        self.update_config_display()
        self.update_sample_rates()

    def update_sample_rates(self):
        self.sample_rate_combo.clear()
        selected_board_id = self.board_selector.currentData()
        selected_board = next((b for b in self.config['boards'] if b['id'] == selected_board_id), None)
        if selected_board:
            board_type = selected_board['type']
            for rate in ADS1X15_DATA_RATES[board_type]:
                self.sample_rate_combo.addItem(str(rate))

    def update_config_display(self):
        config_text = "Loaded Configuration:\n\n"
        for board in self.config['boards']:
            if board['type'] in ['ADS1115', 'ADS1015']:
                config_text += f"- {board['label']} ({board['id']})\n"
                config_text += f"  Type: {board['type']}\n"
                config_text += f"  I2C Address: {board['i2c_address']}\n"
                connected_devices = [d for d in self.config['devices'] if d['connection']['board'] == board['id']]
                if connected_devices:
                    config_text += "  Connected Devices:\n"
                    for device in connected_devices:
                        pin = device['connection'].get('pin', device['connection'].get('pins', ['N/A'])[0])
                        config_text += f"    - {device['label']} (Pin: {pin})\n"
                config_text += "\n"
        self.config_display.setText(config_text)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel, QProgressBar, QTextEdit {
                background-color: #3b3b3b;
                border: 1px solid #5b5b5b;
                padding: 2px;
            }
            QPushButton, QComboBox, QSpinBox {
                background-color: #3b3b3b;
                border: 1px solid #5b5b5b;
                padding: 5px;
            }
            QPushButton:hover, QComboBox:hover, QSpinBox:hover {
                background-color: #4b4b4b;
            }
            QTextEdit {
                font-family: 'Courier New', monospace;
            }
        """)

    def start_collection(self):
        selected_board_id = self.board_selector.currentData()
        selected_board = next((b for b in self.config['boards'] if b['id'] == selected_board_id), None)
        if not selected_board:
            QMessageBox.warning(self, "Error", "No board selected")
            return

        duration = self.duration_spin.value()
        sample_rate = int(self.sample_rate_combo.currentText())

        pin_assignments = {}
        for device in self.config['devices']:
            if device['connection']['board'] == selected_board_id:
                pin = device['connection'].get('pin')
                if pin is not None:
                    pin_assignments[pin] = device.get('label', f"Pin {pin}")

        # Ensure all pins have a label, even if not assigned to a device
        for pin in range(4):  # ADS1x15 has 4 pins
            if pin not in pin_assignments:
                pin_assignments[pin] = f"Pin {pin}"

        self.data_collector = DataCollector(selected_board, pin_assignments, duration, sample_rate)
        self.data_collector.progress_updated.connect(self.update_progress)
        self.data_collector.error_count_updated.connect(self.update_error_count)
        self.data_collector.quality_updated.connect(self.update_qualities)
        self.data_collector.collection_finished.connect(self.handle_collection_finished)
        self.data_collector.io_error_occurred.connect(self.handle_io_error)

        self.collector_thread = QThread()
        self.data_collector.moveToThread(self.collector_thread)
        self.collector_thread.started.connect(self.data_collector.collect_voltage_readings)
        self.collector_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Collecting")

    def stop_collection(self):
        if hasattr(self, 'data_collector'):
            self.data_collector.stop_collection()
        self.status_label.setText("Status: Stopping...")
        self.stop_button.setEnabled(False)

    def handle_collection_finished(self, data, metadata):
        save_data(data, metadata, metadata['device_id'])
        self.collector_thread.quit()
        self.collector_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.error_count_label.setText("Errors: 0")
        self.quality_label.setText("Quality: 100% : 100% : 100% : 100%")
        self.status_label.setText("Status: Idle")
        QMessageBox.information(self, "Collection Complete", "Data collection has finished successfully.")

    def handle_io_error(self, error_message):
        self.stop_collection()
        QMessageBox.critical(self, "I/O Error", f"An I/O error occurred: {error_message}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_error_count(self, count):
        self.error_count_label.setText(f"Errors: {count}")

    def update_qualities(self, qualities):
        quality_str = "Quality: " + " : ".join(f"{q:.0%}" for q in qualities)
        self.quality_label.setText(quality_str)

if __name__ == "__main__":
    app = QApplication([])
    gui = VoltageCollectorGUI()
    gui.show()
    app.exec()