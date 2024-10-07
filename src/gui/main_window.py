# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton
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

        # Add GUI Buttons Section
        self.gui_buttons_layout = QVBoxLayout()
        gui_buttons_group = QWidget()
        gui_buttons_group.setLayout(self.gui_buttons_layout)
        self.gui_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.devices_layout.addWidget(gui_buttons_group)

        self.gui_button_widgets = {}

        # Initialize GUI Buttons if enabled
        if self.app_state.device_manager.use_devices.get("USE_GUI_BUTTONS", False):
            for button_id, gui_button in self.app_state.device_manager.gui_button_manager.items():
                button = QPushButton(gui_button.label)
                button.setCheckable(True)
                button.clicked.connect(lambda checked, b=gui_button: self.on_gui_button_clicked(b, checked))
                self.gui_buttons_layout.addWidget(button)
                self.gui_button_widgets[button_id] = button

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

    def on_gui_button_clicked(self, gui_button, checked):
        gui_button.toggle()
        button_widget = self.gui_button_widgets[gui_button.button_id]
        button_widget.setChecked(gui_button.state)
        button_widget.setStyleSheet("background-color: lightgreen;" if gui_button.state else "")
