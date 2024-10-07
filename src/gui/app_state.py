from PyQt6.QtCore import QObject, pyqtSignal

class AppState(QObject):
    gui_button_state_changed = pyqtSignal(str, bool)  # button_id, new_state

    def __init__(self, board_manager, device_manager):
        super().__init__()
        self.board_manager = board_manager
        self.device_manager = device_manager

    def get_all_gui_buttons(self):
        return self.device_manager.gui_button_manager.gui_buttons

    def get_gui_button_state(self, button_id):
        return self.device_manager.gui_button_manager.get_button_state(button_id)

    def update(self):
        self.device_manager.update()
