import json
import logging
import os
import time
from datetime import datetime
from loguru import logger

class Gate:
    def __init__(self, name, gate_info, boards):
        self.name = name
        board_id = gate_info['io_location']['board']
        self.board = boards.get(board_id)

        if self.board is None:
            raise ValueError(f"💢 Board with ID {board_id} not found")

        self.pin = gate_info['io_location']['pin']
        self.min_angle = gate_info['min']
        self.max_angle = gate_info['max']
        self.status = gate_info['status']
        self.previous_status = gate_info['status']

        if not hasattr(self.board, 'set_servo_angle'):
            logger.warning(f"🌟 Board {board_id} for gate {self.name} does not support servo control.")

    def angle_to_pwm(self, angle):
        """Convert a given angle (0-180) to a PWM value."""
        min_pulse = 1000  # Minimum pulse width (in microseconds)
        max_pulse = 2000  # Maximum pulse width (in microseconds)
        pulse_range = max_pulse - min_pulse
        angle_range = 180  # Full range of servo angles (typically 0-180 degrees)

        pulse_width = min_pulse + (pulse_range * angle / angle_range)
        return int((pulse_width * 65535) / (1000000 / self.board.pca.frequency))

    def stop_servo(self):
        """Stop sending PWM signal to the servo, effectively turning it off."""
        self.board.set_pwm_value(self.pin, 0)
        #logger.debug(f"🔌 Servo on pin {self.pin} has been turned off.")

    def open(self):
        try:
            pwm_value = self.angle_to_pwm(self.max_angle)
            self.board.set_pwm_value(self.pin, pwm_value)
            self.update_status("open")
        except Exception as e:
            logger.error(f"💢 Failed to open gate {self.name}: {e}")

    def close(self):
        try:
            logger.debug(f'      🚥 ⛩️  Closing {self.name}')
            pwm_value = self.angle_to_pwm(self.min_angle)
            self.board.set_pwm_value(self.pin, pwm_value)
            self.update_status("closed")
        except Exception as e:
            logger.error(f"💢 Failed to close gate {self.name}: {e}")

    def update_status(self, new_status):
        if self.previous_status != new_status:
            self.previous_status = new_status
            self.status = new_status
            logger.info(f"⛩️ 🔮 Gate {self.name} {new_status}.")

    def identify(self):
        if hasattr(self.board, 'set_pwm_value'):
            for _ in range(20):
                pwm_value_low = self.angle_to_pwm(80)
                pwm_value_high = self.angle_to_pwm(100)
                self.board.set_pwm_value(self.pin, pwm_value_low)
                time.sleep(0.2)
                self.board.set_pwm_value(self.pin, pwm_value_high)
                time.sleep(0.2)
            if self.status == 'open':
                self.open()
            else:
                self.close()
