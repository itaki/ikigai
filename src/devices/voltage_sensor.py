import numpy as np
from loguru import logger
import time

class VoltageSensor:
    def __init__(self, config, app_config):
        self.id = config['id']
        self.label = config['label']
        self.board_id = config['connection']['board']
        self.pin = config['connection']['pin']
        self.window_size = app_config['VOLTAGE_SENSOR_SETTINGS']['WINDOW_SIZE']
        self.sd_threshold = config['preferences'].get('rolling_sd_threshold', 
                                                      app_config['VOLTAGE_SENSOR_SETTINGS']['DEFAULT_THRESHOLD'])
        self.max_errors = app_config['VOLTAGE_SENSOR_SETTINGS']['MAX_ERRORS']
        
        self.readings = []
        self.state = 'off'
        self.error_count = 0
        self.status = "Initializing"
        self.is_calibrated = False

    def set_board(self, board):
        self.board = board

    def update(self):
        if not hasattr(self, 'board') or self.board is None:
            logger.error(f"❌ Board not set for Voltage Sensor {self.id}")
            return False

        try:
            self.readings = self.board.get_readings(self.pin)[-self.window_size:]
            if not self.is_calibrated:
                self.calibrate()
                return False

        except Exception as e:
            logger.error(f"❌ Error reading from board for Voltage Sensor {self.id}: {e}")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.reset()
            return False

        self.error_count = 0
        return self.check_state()

    def calibrate(self):
        if len(self.readings) < self.window_size:
            return False  # Not enough readings yet
        
        current_std = np.std(self.readings)
        if np.isnan(current_std):
            logger.warning(f"❌ {self.id} has NaN standard deviation. Readings: {len(self.readings)}")
            return False

        if self.sd_threshold > current_std:
            self.is_calibrated = True
            logger.info(f"✅ Calibrated Voltage Sensor {self.id}. Threshold set to {self.sd_threshold:.6f}V")
            return True
        else:
            logger.warning(f"❌ {self.id} Current std: {current_std:.6f}V, threshold: {self.sd_threshold:.6f}V")
            return False

    def check_state(self):
        current_std = np.std(self.readings)
        new_state = 'on' if current_std > self.sd_threshold else 'off'
        
        if new_state != self.state:
            self.state = new_state
            logger.info(f"⚡ {self.label} state changed to: {self.state.upper()}")
            logger.debug(f"⚡ current std: {current_std:.6f}V, threshold: {self.sd_threshold:.6f}V")
            return True

        return False

    def get_state(self):
        return self.state

    def get_status(self):
        return {
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "sd_threshold": self.sd_threshold,
            "current_std": np.std(self.readings) if self.readings else None,
            "status": self.status,
            "is_calibrated": self.is_calibrated
        }

    def cleanup(self):
        self.status = "Cleaned up"

    def reset(self):
        self.readings = []
        self.state = 'off'
        self.error_count = 0
        self.status = "Reset"
        self.is_calibrated = False
        logger.info(f"🔄 Voltage Sensor {self.id} reset")
