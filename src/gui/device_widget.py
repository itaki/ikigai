from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class DeviceWidget(QWidget):
    def __init__(self, device_id, device):
        super().__init__()
        self.device_id = device_id
        self.device = device
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.name_label = QLabel(self.device.get('label', 'Unknown Device'))
        self.state_label = QLabel('State: Unknown')
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.state_label)
        
        self.setLayout(layout)

    def update_state(self, new_state):
        self.state_label.setText(f"State: {new_state}")
