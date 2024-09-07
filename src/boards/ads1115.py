import time
import threading
from loguru import logger
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS

ADS_PIN_NUMBERS = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}

class ADS1115:
    def __init__(self, i2c, config, app_config):
        self.i2c = i2c
        self.board_id = config['id']
        self.i2c_address = int(config['i2c_address'], 16)
        self.label = config.get('label', 'Unknown')
        self.location = config.get('location', 'Unknown')
        self.purpose = config.get('purpose', 'Unknown')
        self.fast_data_rate = app_config['ADS1115_SETTINGS']['FAST_DATA_RATE']
        self.normal_data_rate = app_config['ADS1115_SETTINGS']['NORMAL_DATA_RATE']
        self.initial_readings = app_config['ADS1115_SETTINGS']['INITIAL_READINGS']
        self.max_readings = app_config['VOLTAGE_SENSOR_SETTINGS']['WINDOW_SIZE']
        self.readings = {pin: [] for pin in range(4)}
        self.is_initialized = False
        self.lock = threading.Lock()
        self._stop_thread = threading.Event()

        try:
            self.ads = ADS.ADS1115(i2c, address=self.i2c_address)
            logger.info(f"🔧 Initializing ADS1115 at address {hex(self.i2c_address)} and board ID {self.board_id} ({self.label}, {self.location}, {self.purpose})")
        except Exception as e:
            logger.error(f"💢 Failed to initialize ADS1115 at address {hex(self.i2c_address)}: {str(e)}")
            raise e

        self.thread = threading.Thread(target=self.poll_pins)
        self.thread.start()

    def read_pins(self, data_rate):
        self.ads.data_rate = data_rate
        logger.info(f"🔄 Getting readings from ADS1115 {self.label} at data rate {data_rate} SPS")
        readings_count = 0
        while not self._stop_thread.is_set():
            for pin in range(4):
                try:
                    reading = AnalogIn(self.ads, ADS_PIN_NUMBERS[pin]).voltage
                    with self.lock:
                        self.readings[pin].append(reading)
                        if len(self.readings[pin]) > self.max_readings:
                            self.readings[pin].pop(0)
                    readings_count += 1
                except Exception as e:
                    logger.error(f"Error reading pin {pin} on ADS1115 {self.label}: {e}")
            
            if not self.is_initialized and readings_count >= self.initial_readings:
                self.is_initialized = True
                logger.info(f"✅ ADS1115 {self.label} initialized with {self.initial_readings} readings")
                break
            
            time.sleep(1.0 / data_rate)

    def poll_pins(self):
        try:
            self.read_pins(self.fast_data_rate)
            logger.info(f"✅ Initial fast readings completed for ADS1115 {self.label}")
            self.read_pins(self.normal_data_rate)
        except Exception as e:
            logger.error(f"💢 Error during polling: {e}")

    def get_readings(self, pin):
        with self.lock:
            return list(self.readings[pin])

    def stop(self):
        logger.info("🛑 Stopping ADS1115 polling thread")
        self._stop_thread.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            logger.warning(f"⚠️ ADConverter polling thread for board {self.board_id} did not stop within the timeout period.")
        else:
            logger.info(f"✅ ADConverter polling thread for board {self.board_id} stopped successfully.")

    def cleanup(self):
        logger.info(f"Cleaning up ADS1115 board {self.board_id}")
        self._stop_thread.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            logger.warning(f"ADS1115 board {self.board_id} thread did not stop within 5 seconds")

# Example usage
if __name__ == "__main__":
    import board
    import busio

    logger.info("🔌 Initializing I2C bus")
    i2c = busio.I2C(board.SCL, board.SDA)
    logger.info("✅ I2C bus initialized")

    # Example board configuration
    board_config = {
        "type": "ADS1115",
        "id": "master_control_ad_converter",
        "label": "Voltage Detector - Master Control",
        "location": "Master Control",
        "i2c_address": "0x48",
        "purpose": "Voltage Sensing"
    }

    ad_converter = ADS1115(i2c, board_config)

    try:
        while True:
            time.sleep(1)
            # Just for demonstration, print out the readings
            for pin in range(4):
                readings = ad_converter.get_readings(pin)
                logger.info(f"Pin {pin} readings: {readings}")

                print("what is this")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    finally:
        ad_converter.stop()
        logger.info("AD Converter stopped.")

