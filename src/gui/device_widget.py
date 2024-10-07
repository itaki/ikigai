from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from loguru import logger
class DeviceWidget(QWidget):
    def __init__(self, device_id, device):
        super().__init__()
        self.device_id = device_id
        self.device = device
        logger.info(f"🖥️ DeviceWidget initializing for device {self.device_id}")
        self.init_ui()
        logger.info(f"🖥️ DeviceWidget initialized for device {self.device_id}")

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Check if the device has a 'label' attribute, otherwise use 'get' method
        if hasattr(self.device, 'label'):
            device_label = self.device.label
        elif hasattr(self.device, 'get'):
            device_label = self.device.get('label', 'Unknown Device')
        else:
            device_label = 'Unknown Device'
        
        self.name_label = QLabel(device_label)
        self.state_label = QLabel('State: Unknown')
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.state_label)
        
        self.setLayout(layout)

    def update_state(self, new_state):
        self.state_label.setText(f"State: {new_state}")
