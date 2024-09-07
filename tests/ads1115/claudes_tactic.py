# tests/ads1115/claudes_tactic.py

import sys
from pathlib import Path
import time
from loguru import logger
import board
import busio

# Add the src directory to the Python path
src_path = Path(__file__).resolve().parent.parent.parent / 'src'
sys.path.append(str(src_path))

from boards.ads1115 import ADS1115

class DeviceStateDetector:
    def __init__(self, ads1115, pin, window_size=100, threshold_percentage=10, on_percentage=90):
        self.ads1115 = ads1115
        self.pin = pin
        self.window_size = window_size
        self.threshold_percentage = threshold_percentage / 100
        self.on_percentage = on_percentage / 100
        self.baseline = None
        self.current_state = 'off'

    def calculate_baseline(self):
        readings = self.ads1115.get_readings(self.pin)
        self.baseline = sum(readings) / len(readings)
        logger.info(f'Baseline calculated: {self.baseline:.4f}V')

    def update_state(self):
        voltages = self.ads1115.get_readings(self.pin)[-self.window_size:]
        
        lower_threshold = self.baseline * (1 - self.threshold_percentage)
        upper_threshold = self.baseline * (1 + self.threshold_percentage)
        
        outside_count = sum(1 for v in voltages if v < lower_threshold or v > upper_threshold)
        outside_percentage = outside_count / len(voltages)

        if self.current_state == 'off' and outside_percentage > self.on_percentage:
            self.current_state = 'on'
            logger.info(f'Device turned ON. Average Voltage: {sum(voltages)/len(voltages):.4f}V')
        elif self.current_state == 'on' and outside_percentage <= self.on_percentage:
            self.current_state = 'off'
            logger.info(f'Device turned OFF. Average Voltage: {sum(voltages)/len(voltages):.4f}V')

    def run_detection(self, duration=60):
        logger.info('Starting device state detection...')
        end_time = time.time() + duration
        while time.time() < end_time:
            self.update_state()
            time.sleep(0.1)

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    
    board_config = {
        "type": "ADS1115",
        "id": "master_control_ad_converter",
        "label": "Voltage Detector - Master Control",
        "location": "Master Control",
        "i2c_address": "0x48",
        "purpose": "Voltage Sensing"
    }
    
    app_config = {
        "ADS1115_SETTINGS": {
            "FAST_DATA_RATE": 860,
            "NORMAL_DATA_RATE": 128,
            "INITIAL_READINGS": 100,
            "MAX_READINGS": 1000
        }
    }

    ads1115 = ADS1115(i2c, board_config, app_config)
    detector = DeviceStateDetector(ads1115, pin=0)  # Assuming we're using pin 0
    
    # Wait for the ADS1115 to initialize
    while not ads1115.is_initialized:
        time.sleep(0.1)
    
    detector.calculate_baseline()
    detector.run_detection()

    ads1115.stop()

if __name__ == '__main__':
    main()
