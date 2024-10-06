from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QLabel, QProgressBar, QSpinBox, 
                             QDoubleSpinBox, QFormLayout, QGroupBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor
from loguru import logger
import time
import sys
from PyQt6.QtWidgets import QApplication
import pandas as pd

# Add this line to import DataCollectionThread and CalibrationTool
from core.data_collection import DataCollectionThread

class CalibrationToolGUI(QWidget):
    def __init__(self, calibration_tool):
        super().__init__()
        self.calibration_tool = calibration_tool
        self.initUI()
        self.load_devices()
        self.apply_dark_theme()

    def initUI(self):
        self.setWindowTitle('Voltage Sensor Calibrator')
        layout = QVBoxLayout()

        self.device_list = QListWidget()
        layout.addWidget(QLabel("Select a voltage sensor to calibrate:"))
        layout.addWidget(self.device_list)

        button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Device")
        self.test_button.clicked.connect(self.test_device)
        button_layout.addWidget(self.test_button)

        self.start_button = QPushButton("Start Calibration")
        self.start_button.clicked.connect(self.start_calibration)
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)

        self.cancel_button = QPushButton("Cancel Calibration")
        self.cancel_button.clicked.connect(self.cancel_calibration)
        self.cancel_button.hide()
        layout.addWidget(self.cancel_button)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Add parameter adjustment controls
        param_group = QGroupBox("Calibration Parameters")
        param_layout = QFormLayout()

        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setRange(0, 5)
        self.threshold_spinbox.setSingleStep(0.01)
        param_layout.addRow("Threshold:", self.threshold_spinbox)

        self.window_size_spinbox = QSpinBox()
        self.window_size_spinbox.setRange(10, 100)
        self.window_size_spinbox.setSingleStep(5)
        param_layout.addRow("Window Size:", self.window_size_spinbox)

        self.percentage_spinbox = QSpinBox()
        self.percentage_spinbox.setRange(10, 90)
        self.percentage_spinbox.setSingleStep(5)
        param_layout.addRow("Percentage:", self.percentage_spinbox)

        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(10, 300)  # 10 seconds to 5 minutes
        self.duration_spinbox.setSingleStep(10)
        self.duration_spinbox.setValue(60)  # Default to 60 seconds
        param_layout.addRow("Test Duration (s):", self.duration_spinbox)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # Add analyze button
        self.analyze_button = QPushButton("Analyze Calibration Data")
        self.analyze_button.clicked.connect(self.analyze_calibration_data)
        layout.addWidget(self.analyze_button)

        self.setLayout(layout)
        logger.info("UI initialized")

    def load_devices(self):
        voltage_sensors = [device for device in self.calibration_tool.devices if device['type'] == 'voltage_sensor']
        logger.info(f"Voltage sensors found: {len(voltage_sensors)}")
        for sensor in voltage_sensors:
            item = QListWidgetItem(f"{sensor['label']} ({sensor['id']})")
            item.setData(Qt.ItemDataRole.UserRole, sensor['id'])
            self.device_list.addItem(item)
            logger.debug(f"Added sensor to list: {sensor['label']} ({sensor['id']})")

        if not voltage_sensors:
            self.status_label.setText("No voltage sensors found in configuration")
            logger.warning("No voltage sensors found in configuration")

    def test_device(self):
        selected_item = self.device_list.currentItem()
        if not selected_item:
            self.status_label.setText("No device selected")
            return

        device_id = selected_item.data(Qt.ItemDataRole.UserRole)
        logger.info(f"Testing device: {device_id}")
        
        device = next((d for d in self.calibration_tool.devices if d['id'] == device_id), None)
        if not device:
            logger.error(f"Device not found in configuration: {device_id}")
            self.status_label.setText(f"Error: Device not found in configuration")
            return

        logger.info(f"Selected device: {device['id']}")
        logger.info(f"Device connected to board: {device['connection']['board']}, pin: {device['connection']['pin']}")

        board = self.calibration_tool.get_board(device['id'])
        if board is None:
            error_msg = f"Failed to get board for device: {device['id']}"
            logger.error(error_msg)
            self.status_label.setText(error_msg)
            return

        try:
            reading = board.get_reading(device['connection']['pin'])
            self.status_label.setText(f"Current reading: {reading:.6f} V")
        except Exception as e:
            error_msg = f"Error reading device: {str(e)}"
            logger.error(error_msg)
            self.status_label.setText(error_msg)

    def start_calibration(self):
        selected_item = self.device_list.currentItem()
        if not selected_item:
            self.status_label.setText("No device selected")
            return

        device_id = selected_item.data(Qt.ItemDataRole.UserRole)
        self.current_device = next((d for d in self.calibration_tool.devices if d['id'] == device_id), None)
        if not self.current_device:
            self.status_label.setText("Selected device not found in configuration")
            return

        board = self.calibration_tool.get_board(device_id)
        if board is None:
            self.status_label.setText(f"Failed to get board for device: {device_id}")
            return

        self.ads = board
        pin = self.current_device['connection']['pin']
        
        self.start_off_calibration()

    def start_off_calibration(self):
        self.status_label.setText("Collecting OFF state data...")
        pin = self.current_device['connection']['pin']
        duration = self.duration_spinbox.value()
        self.collection_thread = DataCollectionThread(self.ads, pin, duration, 860)
        self.collection_thread.progress_update.connect(self.update_progress)
        self.collection_thread.collection_complete.connect(self.off_calibration_complete)
        self.collection_thread.error_occurred.connect(self.handle_error)
        self.collection_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        logger.debug(f"Progress updated: {value}%")

    def handle_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        logger.error(f"Data collection error: {error_message}")
        self.cancel_calibration()  # Optionally cancel the calibration process

    def off_calibration_complete(self, data):
        self.off_data = data
        self.status_label.setText("OFF calibration complete. Prepare device for ON state and click Start.")
        self.start_button.setText("Start ON Calibration")
        self.start_button.show()
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.prepare_on_calibration)

    def prepare_on_calibration(self):
        self.start_button.hide()
        self.status_label.setText("Preparing for ON state calibration...")
        self.progress_bar.setValue(0)
        QTimer.singleShot(5000, self.start_on_calibration)

    def start_on_calibration(self):
        self.status_label.setText("Collecting ON state data...")
        pin = self.current_device['connection']['pin']
        duration = self.duration_spinbox.value()
        self.collection_thread = DataCollectionThread(self.ads, pin, duration, 128)
        self.collection_thread.progress_update.connect(self.update_progress)
        self.collection_thread.collection_complete.connect(self.on_calibration_complete)
        self.collection_thread.error_occurred.connect(self.handle_error)
        self.collection_thread.start()

    def on_calibration_complete(self, data):
        self.on_data = data
        self.analyze_calibration_data()
        filename = self.calibration_tool.save_calibration_data_xml(self.current_device, self.off_data, self.on_data)
        if filename:
            self.status_label.setText(f"Calibration complete! Data saved to {filename}")
        else:
            self.status_label.setText("Calibration complete, but failed to save data.")
        self.cancel_button.hide()
        self.start_button.setText("Start New Calibration")
        self.start_button.show()
        self.test_button.show()
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.start_calibration)

    def analyze_calibration_data(self):
        if not hasattr(self, 'off_data') or not hasattr(self, 'on_data') or not hasattr(self, 'current_device'):
            self.status_label.setText("Please perform calibration first")
            logger.warning("Attempted to analyze data before calibration")
            return

        try:
            results, (off_filename, on_filename, analysis_filename) = self.calibration_tool.analyze_calibration_data(
                self.current_device, self.off_data, self.on_data
            )

            self.threshold_spinbox.setValue(results['optimal_threshold'])
            self.window_size_spinbox.setValue(results['optimal_window_size'])
            self.percentage_spinbox.setValue(results['optimal_percentage'])

            status_text = (f"Analysis complete. Optimal parameters: "
                           f"Threshold={results['optimal_threshold']:.2f}, "
                           f"Window Size={results['optimal_window_size']}, "
                           f"Percentage={results['optimal_percentage']}%\n"
                           f"OFF data saved to: {off_filename}\n"
                           f"ON data saved to: {on_filename}\n"
                           f"Analysis image saved to: {analysis_filename}")
            
            self.status_label.setText(status_text)
            logger.info(f"Calibration data analyzed: {results}")
        except Exception as e:
            self.status_label.setText(f"Error analyzing calibration data: {str(e)}")
            logger.error(f"Error in analyze_calibration_data: {e}", exc_info=True)

    def cancel_calibration(self):
        if hasattr(self, 'collection_thread'):
            self.collection_thread.quit()
            self.collection_thread.wait()
        self.start_button.setText("Start Calibration")
        self.start_button.show()
        self.cancel_button.hide()
        self.test_button.show()
        self.status_label.setText("Calibration cancelled")
        logger.info("Calibration cancelled")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #272822;
                color: #F8F8F2;
                font-family: Consolas, Monaco, 'Courier New', monospace;
            }
            QListWidget {
                background-color: #3E3D32;
                border: 1px solid #75715E;
            }
            QListWidget::item:selected {
                background-color: #49483E;
            }
            QPushButton {
                background-color: #49483E;
                border: 1px solid #75715E;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #75715E;
            }
            QProgressBar {
                border: 1px solid #75715E;
                background-color: #3E3D32;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #A6E22E;
            }
        """)

        # Set the application palette for elements not covered by the stylesheet
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(39, 40, 34))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(248, 248, 242))
        palette.setColor(QPalette.ColorRole.Base, QColor(39, 40, 34))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(62, 61, 50))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(39, 40, 34))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(248, 248, 242))
        palette.setColor(QPalette.ColorRole.Text, QColor(248, 248, 242))
        palette.setColor(QPalette.ColorRole.Button, QColor(73, 72, 62))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(248, 248, 242))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(166, 226, 46))
        palette.setColor(QPalette.ColorRole.Link, QColor(166, 226, 46))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(73, 72, 62))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(248, 248, 242))
        self.setPalette(palette)

    def handle_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        logger.error(f"Data collection error: {error_message}")
        self.cancel_calibration()  # Optionally cancel the calibration process

if __name__ == '__main__':
    logger.info("Starting Voltage Sensor Calibrator application")
    app = QApplication(sys.argv)
    ex = CalibrationTool()
    ex.show()
    logger.info("Application window shown")
    sys.exit(app.exec())