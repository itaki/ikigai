from PyQt6.QtCore import QObject, pyqtSignal
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GuiButton(QObject):
    state_changed = pyqtSignal(str, bool)  # button_id, new_state

    def __init__(self, button_config, device_manager):
        super().__init__()
        self.button_id = button_config['id']
        self.label = button_config['label']
        self.gate_prefs = button_config['preferences'].get('gate_prefs', [])
        self.use_collector = button_config['preferences'].get('use_collector', [])
        self.spin_down_time = button_config['preferences'].get('spin_down_time', 0)
        self.device_manager = device_manager
        self.state = False  # False: Off, True: On
        self._parent_manager = None  # Add this line
        self.last_activated = None  # Add this line

    def set_parent_manager(self, manager):
        self._parent_manager = manager  # Add this method

    def get_state(self):
        return self.state

    def toggle(self):
        self.state = not self.state
        self.state_changed.emit(self.button_id, self.state)
        if self.state:
            self.activate()
        else:
            self.deactivate()

    def activate(self):
        self.state = True
        self.last_activated = time.time()
        logger.info(f"🖱️ GUI Button '{self.label}' activated")
        self.state_changed.emit(self.button_id, self.state)

    def deactivate(self):
        self.state = False
        logger.info(f"🖱️ GUI Button '{self.label}' deactivated")
        self.state_changed.emit(self.button_id, self.state)
