# src/gui/button_widget.py

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

class ButtonWidget(QWidget):
    """Represents a GUI button in the Shop Management System."""
    toggled = pyqtSignal(bool)

    def __init__(self, gui_button):
        super().__init__()
        self.gui_button = gui_button

        # Initialize the button
        self.button = QPushButton(self.gui_button.label)
        self.button.setCheckable(True)
        self.button.setChecked(self.gui_button.state)
        self.button.clicked.connect(self.on_button_clicked)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

        # Update the visual state
        self.update_state(self.gui_button.state)

    def on_button_clicked(self):
        self.gui_button.toggle()

    def update_state(self, state):
        self.button.setChecked(state)
        if state:
            self.button.setStyleSheet('background-color: lightgreen;')
        else:
            self.button.setStyleSheet('')
