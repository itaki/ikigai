from loguru import logger
import threading
import time
from .gate_manager import GateManager
from .voltage_sensor_manager import VoltageSensorManager
from .button_manager import ButtonManager
from .rgbled_manager import RGBLEDManager
from .dust_collector_manager import DustCollectorManager

class DeviceManager:
    def __init__(self, device_config, gates_config, boards, rgbled_styles, app_config):
        self.use_devices = app_config.get('USE_DEVICES', {})
        self.device_config = device_config
        self.gates_config = gates_config
        self.boards = boards
        self.rgbled_styles = rgbled_styles
        self.app_config = app_config
        self.stop_event = threading.Event()
        logger.info("🔧 Initializing DeviceManager")
        self.gate_manager = None
        self.voltage_sensor_manager = None
        self.button_manager = None
        self.rgbled_manager = None
        self.dust_collector_manager = None
        self.previous_voltage_states = {}
        self.previous_button_states = {}
        self.previous_led_states = {}
        self.initialize_devices()

    def initialize_devices(self):
        try:
            logger.info(f"🔧 Available boards: {list(self.boards.keys())}")

            if self.use_devices.get("USE_GATES", False):
                self.gate_manager = GateManager(self.boards, self.gates_config)
                logger.info("⛩️ GateManager initialized")

            if self.use_devices.get("USE_BUTTONS", False):
                self.button_manager = ButtonManager(self.device_config, self.boards)
                self.button_manager.start_polling()
                logger.info("🔘 ButtonManager initialized and polling started")

            if self.use_devices.get("USE_RGB_LEDS", False):
                self.rgbled_manager = RGBLEDManager(self.device_config, self.boards, self.rgbled_styles)
                logger.info("💡 RGBLEDManager initialized")

            if self.use_devices.get("USE_DUST_COLLECTORS", False):
                self.dust_collector_manager = DustCollectorManager(self.device_config)
                logger.info("💨 DustCollectorManager initialized")

            if self.use_devices.get("USE_VOLTAGE_SENSORS", False):
                self.voltage_sensor_manager = VoltageSensorManager(self.device_config, self.boards, self.app_config)
                logger.info("⚡ VoltageSensorManager initialized")

        except Exception as e:
            logger.error(f"💢 Error initializing devices: {str(e)}")
            raise e

    def update(self):
        try:
            state_changed = False
            current_voltage_states = {}
            current_button_states = {}

            if self.use_devices.get("USE_VOLTAGE_SENSORS", False) and self.voltage_sensor_manager:
                voltage_state_changed = self.voltage_sensor_manager.update()
                current_voltage_states = self.voltage_sensor_manager.get_all_sensor_statuses()
                if voltage_state_changed:
                    changed_sensors = [f"{k}: {v['state']}" for k, v in current_voltage_states.items() if self.previous_voltage_states.get(k, {}).get('state') != v['state']]
                    if changed_sensors:
                        logger.info(f"⚡ Voltage sensor state changed: {', '.join(changed_sensors)}")
                        state_changed = True

            if self.use_devices.get("USE_BUTTONS", False) and self.button_manager:
                current_button_states = self.button_manager.get_all_button_statuses()
                if current_button_states != self.previous_button_states:
                    state_changed = True
                    changed_buttons = [f"{k}: {v}" for k, v in current_button_states.items() if self.previous_button_states.get(k) != v]
                    logger.info(f"🔘 Button state changed: {', '.join(changed_buttons)}")

            # Update dust collectors regardless of state change
            if self.use_devices.get("USE_DUST_COLLECTORS", False) and self.dust_collector_manager:
                self.dust_collector_manager.update_collector_state(current_voltage_states, current_button_states)

            # Only update gates if there's a state change
            if state_changed and self.use_devices.get("USE_GATES", False) and self.gate_manager:
                gates_to_open = self.get_gates_to_open(current_voltage_states, current_button_states)
                self.gate_manager.set_gates(gates_to_open)

            if self.use_devices.get("USE_RGB_LEDS", False) and self.rgbled_manager:
                self.update_rgbleds(current_voltage_states, current_button_states)

            self.previous_voltage_states = current_voltage_states
            self.previous_button_states = current_button_states

        except Exception as e:
            logger.error(f"💢 Error during device update: {str(e)}")
            raise e

    def log_system_status(self):
        logger.info("📊 System Status:")
        if self.voltage_sensor_manager:
            for sensor_id, status in self.voltage_sensor_manager.get_all_sensor_statuses().items():
                logger.info(f"  ⚡ {status['label']}: {status['state']} (Calibrated: {status['is_calibrated']})")
        if self.button_manager:
            for button_id, status in self.button_manager.get_all_button_statuses().items():
                logger.info(f"  🔘 {button_id}: {status}")

    def get_gates_to_open(self, voltage_states, button_states):
        gates_to_open = set()
        
        for sensor_id, status in voltage_states.items():
            if status['state'] == 'on':
                sensor_config = next((device for device in self.device_config if device['id'] == sensor_id), None)
                if sensor_config and 'preferences' in sensor_config and 'gate_prefs' in sensor_config['preferences']:
                    gates_to_open.update(sensor_config['preferences']['gate_prefs'])
        
        for button_id, status in button_states.items():
            if status == 'on':
                button_config = next((device for device in self.device_config if device['id'] == button_id), None)
                if button_config and 'preferences' in button_config and 'gate_prefs' in button_config['preferences']:
                    gates_to_open.update(button_config['preferences']['gate_prefs'])
        
        return list(gates_to_open)

    def update_rgbleds(self, voltage_states, button_states):
        current_led_states = {}
        for led_id, led in self.rgbled_manager.rgb_leds.items():
            led_state = 'off'
            for listen_to_id in led.listen_to:
                if button_states.get(listen_to_id) == 'on' or voltage_states.get(listen_to_id) == 'on':
                    led_state = 'on'
                    break
            current_led_states[led_id] = led_state

        changed_leds = []
        for led_id, state in current_led_states.items():
            if state != self.previous_led_states.get(led_id):
                self.rgbled_manager.set_led_state(led_id, state)
                changed_leds.append(f"{led_id}: {state}")

        if changed_leds:
            logger.info(f"💡 LED states changed: {', '.join(changed_leds)}")

        self.previous_led_states = current_led_states

    def cleanup(self):
        logger.info("🧹 Cleaning up DeviceManager")
        for manager in [self.voltage_sensor_manager, self.button_manager, self.gate_manager, self.rgbled_manager, self.dust_collector_manager]:
            if manager and hasattr(manager, 'cleanup'):
                try:
                    manager.cleanup()
                except Exception as e:
                    logger.error(f"Error during cleanup of {type(manager).__name__}: {str(e)}")
        if hasattr(self, 'board_manager'):
            self.board_manager.cleanup()
        logger.info("✅ DeviceManager cleanup completed")

    def start_monitoring(self):
        try:
            logger.info("🔍 Starting monitoring")
            if self.voltage_sensor_manager:
                self.voltage_sensor_manager.start_monitoring()
            if self.button_manager:
                self.button_manager.start_polling()
        except Exception as e:
            logger.error(f"💢 Error starting monitoring: {str(e)}")