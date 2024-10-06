# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from .device_widget import DeviceWidget

class MainWindow(QMainWindow):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.init_ui()
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_devices)
        self.update_timer.start(100)  # Update every 100ms

    def init_ui(self):
        self.setWindowTitle('Shop Management System')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel('Shop Management System', alignment=Qt.AlignmentFlag.AlignCenter))
        main_layout.addLayout(header_layout)
        
        # Devices Grid
        self.devices_layout = QGridLayout()
        self.update_device_widgets()
        main_layout.addLayout(self.devices_layout)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel('System Status: Running', alignment=Qt.AlignmentFlag.AlignLeft))
        main_layout.addLayout(footer_layout)

    def update_device_widgets(self):
        devices = self.app_state.get_all_devices()
        for i, (device_id, device) in enumerate(devices.items()):
            widget = DeviceWidget(device_id, device)
            widget.setObjectName(device_id)
            self.devices_layout.addWidget(widget, i // 3, i % 3)

    def update_devices(self):
        self.app_state.update()
        devices = self.app_state.get_all_devices()
        for device_id, device in devices.items():
            widget = self.findChild(DeviceWidget, device_id)
            if widget:
                widget.update_state(self.app_state.get_device_state(device_id))
