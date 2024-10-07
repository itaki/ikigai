# gui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from .button_widget import ButtonWidget
from loguru import logger

class MainWindow(QMainWindow):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.gui_button_widgets = {}
        logger.info("🖥️ MainWindow initializing")
        self.init_ui()

        # Set up the update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_gui_buttons)
        self.update_timer.start(100)  # Update every 100ms

    def init_ui(self):
        self.setWindowTitle('Shop Management System')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Header
        header_label = QLabel('Shop Management System')
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # GUI Buttons Grid
        self.gui_buttons_layout = QGridLayout()
        main_layout.addLayout(self.gui_buttons_layout)
        self.add_gui_buttons()

        # Footer
        footer_label = QLabel('System Status: Running')
        footer_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(footer_label)

    def add_gui_buttons(self):
        gui_buttons = self.app_state.device_manager.gui_button_manager.gui_buttons
        for i, (button_id, gui_button) in enumerate(gui_buttons.items()):
            button_widget = ButtonWidget(gui_button)
            self.gui_buttons_layout.addWidget(button_widget, i // 3, i % 3)
            self.gui_button_widgets[button_id] = button_widget

    def update_gui_buttons(self):
        for button_id, button_widget in self.gui_button_widgets.items():
            button_widget.update_state(self.app_state.get_gui_button_state(button_id))
