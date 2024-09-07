import time
import threading
import logging
import os
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Constants
NUM_SAMPLES = 50
SENSOR_DETECTION_THRESHOLD = 1.6
ERROR_THRESHOLD = 2.5
TRIGGER_THRESHOLD = 1.003
ADS_PIN_NUMBERS = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example JSON configuration
config = {
    "volt": {
        "label": "VS for miter saw",
        "type": "ADS1115",
        "version": "20 amp",
        "voltage_address": {
            "board_address": "0x48",
            "pin": 0
        },
        "multiplier": 3,
        "status": "off"
    }
}

class Voltage_Sensor:
    def __init__(self, volt, sensor_detection_threshold=SENSOR_DETECTION_THRESHOLD, error_threshold=ERROR_THRESHOLD, min_readings=NUM_SAMPLES):
        self.label = volt.get('label', 'unknown')
        self.board_address = int(volt['voltage_address']['board_address'], 16)
        self.pin_number = ADS_PIN_NUMBERS[volt['voltage_address']['pin']]
        self.sensor_detection_threshold = sensor_detection_threshold
        self.error_threshold = error_threshold
        self.min_readings = min_readings
        self.readings = []
        self.error_raised = False
        self.sensor_exists = True
        self.board_exists = None
        self.trigger = None
        self.lock = threading.Lock()
        self._stop_thread = False

        try:
            self.chan = AnalogIn(ADS.ADS1115(i2c, address=self.board_address), self.pin_number)
            print(f"Type of self.chan: {type(self.chan)}")
            self.board_exists = True
            logger.info(f"     🔮 Adding Voltage Sensor on pin {self.pin_number} on ADS1115 at address {hex(self.board_address)}")
            reading = self.get_reading()
            logger.info(f"     🔮 Current voltage reading is {reading}")
            self.set_trigger_voltage()
            self.thread = threading.Thread(target=self.collect_readings)
            self.thread.start()
        except Exception as e:
            logger.error(f"💢 ADS1115 not found at {hex(self.board_address)}. Cannot create voltage sensor")
            self.board_exists = False
            logger.exception(e)

    def get_reading(self):
        if self.board_exists:
            reading = self.chan.voltage
            with self.lock:
                self.readings.append(reading)
                if len(self.readings) > self.min_readings:
                    self.readings.pop(0)
                max_reading = max(self.readings)
                self.reading = max_reading
            return max_reading
        else:
            return 0

    def collect_readings(self):
        while not self._stop_thread:
            self.get_reading()
            time.sleep(0.001)

    def in_good_range(self):
        if self.sensor_detection_threshold < self.reading < self.error_threshold:
            self.error_raised = False
            self.sensor_exists = True
            return True
        elif not self.error_raised:
            self.error_raised = True
            if self.sensor_detection_threshold > self.reading:
                logger.warning(f"🌟 No sensor on pin {self.pin_number} at address {hex(self.board_address)}")
            if self.reading > self.error_threshold:
                logger.warning(f"🌟 Problem with sensor on pin {self.pin_number} at address {hex(self.board_address)}")
        self.sensor_exists = False
        return False

    def am_i_on(self):
        if self.board_exists:
            reading = self.reading
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
        reading = self.reading
        if self.in_good_range():
            self.trigger = reading * TRIGGER_THRESHOLD
            logger.info(f"     🔮 Setting trigger point on pin {self.pin_number} at address {hex(self.board_address)} to {self.trigger}")

    def stop(self):
        self._stop_thread = True
        self.thread.join()

if __name__ == "__main__":
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    sensor_config = config["volt"]
    voltage_sensor = Voltage_Sensor(sensor_config)

    try:
        while True:
            is_on = voltage_sensor.am_i_on()
            status = "ON" if is_on else "OFF"
            logger.info(f"     🔮 Tool is {status}")
            time.sleep(0.001)  # Reduced delay to make it run faster
    except KeyboardInterrupt:
        voltage_sensor.stop()
