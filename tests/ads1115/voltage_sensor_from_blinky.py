import os
import sys
import json
import board
import busio
import time
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

ads_pin_numbers = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_FILE = os.path.join(BASE_DIR, 'blinky_config.json')

class Voltage_sensor:
    def __init__(self, volt, sensor_detection_threshold=1.6, error_threshold=2.5, min_readings=10):
        self.board_address = int(volt['voltage_address']['board_address'], 16)
        self.pin_number = ads_pin_numbers[volt['voltage_address']['pin']]
        self.sensor_detection_threshold = sensor_detection_threshold
        self.error_threshold = error_threshold
        self.sensor_exists = True
        self.min_readings = min_readings
        self.readings = []
        self.error_raised = False
        self.board_exists = None
        try:
            self.chan = AnalogIn(ADS.ADS1115(i2c, address=self.board_address), self.pin_number)
            self.board_exists = True
            print(f"-----> Adding Voltage Sensor on pin {self.pin_number} on ADS1115 at address {hex(self.board_address)}")
            reading = self.get_reading()
            print(f"        Current voltage reading is {reading}")
            self.set_trigger_voltage()
        except:
            print(f"■■■■■ ERROR! ■■■■■■ ADS1115 not found at {hex(self.board_address)}. Cannot create voltage sensor")
            self.board_exists = False

    def get_reading(self):
        if self.board_exists:
            reading = self.chan.voltage
            self.readings.append(reading)
            if len(self.readings) > self.min_readings:
                self.readings.pop(0)
            max_reading = max(self.readings)
            self.reading = max_reading
            return max_reading
        else:
            return 0

    def in_good_range(self):
        if self.sensor_detection_threshold < self.reading < self.error_threshold:
            self.error_raised = False
            self.sensor_exists = True
            return True
        elif not self.error_raised:
            self.error_raised = True
            if self.sensor_detection_threshold > self.reading:
                print(f"◍◍◍◍ CAUTION!!!!! No sensor on pin {self.pin_number} at address {hex(self.board_address)}")
            if self.reading > self.error_threshold:
                print(f"◍◍◍◍ CAUTION!!!!! Problem with sensor on pin {self.pin_number} at address {hex(self.board_address)}")
        self.sensor_exists = False
        return False

    def am_i_on(self):
        if self.board_exists:
            reading = self.get_reading()
            if self.in_good_range() and self.sensor_exists:
                return reading > self.trigger
            elif self.in_good_range():
                self.set_trigger_voltage()
                return self.am_i_on()
            else:
                return False
        else:
            return False

    def set_trigger_voltage(self):
        reading = self.get_reading()
        if self.in_good_range():
            self.trigger = reading * 1.003
            print(f"Setting trigger point on pin {self.pin_number} at address {hex(self.board_address)} to {self.trigger}")

