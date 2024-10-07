from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal
from devices.gui_button import GuiButton
import json

class GuiButtonManager(QObject):
    button_state_changed = pyqtSignal(str, bool)  # button_id, new_state

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.gui_buttons = {}
        self.load_gui_buttons_config()

    def load_gui_buttons_config(self):
        config_path = 'src/config/gui_buttons.json'
        try:
            with open(config_path, 'r') as f:
                gui_buttons_config = json.load(f)
            
            for button_config in gui_buttons_config:
                gui_button = GuiButton(button_config, self.device_manager)
                gui_button.set_parent_manager(self)  # Set the parent manager
                gui_button.state_changed.connect(self.handle_gui_button_state_change)
                self.gui_buttons[gui_button.button_id] = gui_button
            
            logger.info("🎛️ GUI Buttons initialized")
        except Exception as e:
            logger.error(f"💥 Failed to load GUI buttons configuration: {e}")

    def handle_gui_button_state_change(self, button_id, new_state):
        logger.info(f"🟢 GUI Button '{button_id}' toggled to {'On' if new_state else 'Off'}")
        self.button_state_changed.emit(button_id, new_state)
        # Additional logic can be added here if needed

    def toggle_button(self, button_id):
        if button_id in self.gui_buttons:
            self.gui_buttons[button_id].toggle()
        else:
            logger.warning(f"Attempted to toggle non-existent GUI button: {button_id}")

    def get_button_state(self, button_id):
        if button_id in self.gui_buttons:
            return self.gui_buttons[button_id].state
        else:
            logger.warning(f"Attempted to get state of non-existent GUI button: {button_id}")
            return None

    def get_all_button_states(self):
        return {button_id: button.state for button_id, button in self.gui_buttons.items()}

    def cleanup(self):
        logger.info("🧹 Cleaning up GuiButtonManager")
        for gui_button in list(self.gui_buttons.values()):
            try:
                if not gui_button.state_changed.receivers():
                    logger.warning(f"Button {gui_button.button_id} has no connected receivers")
                else:
                    gui_button.state_changed.disconnect()
            except RuntimeError:
                logger.warning(f"Button {gui_button.button_id} has already been deleted")
        self.gui_buttons.clear()
        logger.info("✅ GuiButtonManager cleanup completed")
