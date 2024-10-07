from PyQt6.QtCore import QObject, pyqtSignal

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

    def set_parent_manager(self, manager):
        self._parent_manager = manager  # Add this method

    def toggle(self):
        self.state = not self.state
        self.state_changed.emit(self.button_id, self.state)
        if self.state:
            self.activate()
        else:
            self.deactivate()

    def activate(self):
        # Activate gates
        for gate_id in self.gate_prefs:
            self.device_manager.gate_manager.open_gate(gate_id)
        # Turn on dust collectors
        for collector_id in self.use_collector:
            self.device_manager.dust_collector_manager.turn_on_collector(collector_id)

    def deactivate(self):
        # Deactivate gates
        for gate_id in self.gate_prefs:
            self.device_manager.gate_manager.close_gate(gate_id)
        # Turn off dust collectors after spin_down_time
        for collector_id in self.use_collector:
            self.device_manager.dust_collector_manager.turn_off_collector_with_delay(collector_id, self.spin_down_time)
