import threading
import time
from loguru import logger
from devices.button import Button

class ButtonManager:
    def __init__(self, device_config, boards):
        self.buttons = {}
        self.boards = boards
        self.stop_event = threading.Event()
        self.debounce_time = 0.05  # 50ms debounce time
        self.polling_thread = None
        self.initialize_buttons(device_config)

    def initialize_buttons(self, device_config):
        for device in device_config:
            if device['type'] == 'button':
                board = self.boards.get(device['connection']['board'])
                if board:
                    button = Button(device, board)
                    self.buttons[device['id']] = button
                    logger.info(f"✅ Button {button.label} initialized on board {device['connection']['board']} at pin {button.pin_number}")
                else:
                    logger.error(f"💢 Board {device['connection']['board']} not found for button {device['label']}")

    def start_polling(self):
        if not self.polling_thread or not self.polling_thread.is_alive():
            self.stop_event.clear()
            self.polling_thread = threading.Thread(target=self._poll_buttons)
            self.polling_thread.start()
            logger.info("🔍 Button polling started")
        else:
            logger.warning("Button polling thread is already running")

    def stop_polling(self):
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_event.set()
            self.polling_thread.join()
            logger.info("🛑 Button polling stopped")
        else:
            logger.warning("No active button polling thread to stop")

    def _poll_buttons(self):
        last_press_time = {button_id: 0 for button_id in self.buttons}
        button_states = {button_id: False for button_id in self.buttons}

        while not self.stop_event.is_set():
            for button_id, button in self.buttons.items():
                try:
                    current_state = button.read_pin()
                    if current_state is None:
                        continue  # Skip this iteration if read_pin returns None

                    if current_state != button_states[button_id]:
                        current_time = time.time()
                        if current_time - last_press_time[button_id] > self.debounce_time:
                            if current_state:  # Button is pressed
                                self._toggle_button_state(button)
                            button_states[button_id] = current_state
                            last_press_time[button_id] = current_time
                except Exception as e:
                    logger.error(f"Error polling button {button.label}: {e}")

            time.sleep(0.01)  # Poll every 10ms

    def _toggle_button_state(self, button):
        button.state = 'on' if button.state == 'off' else 'off'
        logger.info(f"Button {button.label} toggled to {button.state}")
        # Here you can add any additional logic or callbacks when a button state changes

    def get_button_status(self, button_id):
        button = self.buttons.get(button_id)
        return button.state if button else None

    def get_all_button_statuses(self):
        return {button_id: button.state for button_id, button in self.buttons.items()}

    def cleanup(self):
        logger.info("🧹 Cleaning up ButtonManager")
        self.stop_polling()
        for button in self.buttons.values():
            button.cleanup()
        logger.info("✅ ButtonManager cleanup completed")
