import numpy as np
from loguru import logger
import time

class VoltageSensor:
    def __init__(self, config, app_config):
        self.id = config['id']
        self.label = config['label']
        self.board_id = config['connection']['board']
        self.pin = config['connection']['pin']
        self.window_size = config['preferences'].get('window_size', app_config['VOLTAGE_SENSOR_SETTINGS']['WINDOW_SIZE'])
        self.threshold_multiplier = config['preferences'].get('threshold_standard_deviation_multiplier', 
                                                              app_config['VOLTAGE_SENSOR_SETTINGS']['DEFAULT_THRESHOLD_DEVIATION'])
        self.activation_trigger_percent = app_config['VOLTAGE_SENSOR_SETTINGS'].get('ACTIVATION_TRIGGER_PERCENT', 50)
        self.max_errors = app_config['VOLTAGE_SENSOR_SETTINGS']['MAX_ERRORS']
        
        self.readings = []
        self.baseline_std = None
        self.threshold = None
        self.state = 'off'
        self.is_calibrated = False
        self.error_count = 0
        self.status = "Initializing"
        self.cooldown_period = 1  # 1 second cooldown
        self.last_calibration_time = 0

    def set_board(self, board):
        self.board = board

    def update(self):
        if not hasattr(self, 'board') or self.board is None:
            logger.error(f"Board not set for Voltage Sensor {self.id}")
            return False

        try:
            new_readings = self.board.get_readings(self.pin)
            if not new_readings:
                logger.error(f"No readings for Voltage Sensor {self.id}")
                return False

            self.readings.extend(new_readings)
            self.readings = self.readings[-self.window_size:]  # Keep only the last 'window_size' readings

        except Exception as e:
            logger.error(f"Error reading from board for Voltage Sensor {self.id}: {e}")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.reset()
            return False

        self.error_count = 0

        if not self.is_calibrated:
            return self.calibrate()

        return self.check_state()

    def calibrate(self):
        if len(self.readings) < self.window_size:
            return False

        self.baseline_std = np.std(self.readings)
        self.threshold = self.baseline_std * self.threshold_multiplier
        self.is_calibrated = True
        self.last_calibration_time = time.time()
        logger.info(f"Voltage Sensor {self.id} calibrated. Baseline Std Dev: {self.baseline_std:.6f}V, Threshold: {self.threshold:.6f}V")
        return True

    def check_state(self):
        if time.time() - self.last_calibration_time < self.cooldown_period:
            return False

        current_std = np.std(self.readings)
        new_state = 'on' if current_std > self.threshold else 'off'
        
        if new_state != self.state:
            self.state = new_state
            logger.info(f"Voltage Sensor {self.id} state changed to: {self.state.upper()}")
            return True

        return False

    def get_state(self):
        return self.state

    def get_status(self):
        return {
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "is_calibrated": self.is_calibrated,
            "baseline_std": self.baseline_std,
            "threshold": self.threshold,
            "current_std": np.std(self.readings) if self.readings else None,
            "status": self.status
        }

    def cleanup(self):
        self.status = "Cleaned up"

    def reset(self):
        self.readings = []
        self.state = 'off'
        self.baseline_std = None
        self.threshold = None
        self.is_calibrated = False
        self.error_count = 0
        self.status = "Reset"
        self.last_calibration_time = 0
        logger.info(f"Voltage Sensor {self.id} reset")
