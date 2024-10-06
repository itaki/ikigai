from PyQt6.QtCore import QObject, pyqtSignal

class AppState(QObject):
    device_state_changed = pyqtSignal(str, dict)  # device_id, new_state

    def __init__(self, board_manager, device_manager):
        super().__init__()
        self.board_manager = board_manager
        self.device_manager = device_manager

    def get_all_devices(self):
        return self.device_manager.get_all_devices()

    def get_device_state(self, device_id):
        return self.device_manager.get_device_state(device_id)

    def update(self):
        self.device_manager.update()
