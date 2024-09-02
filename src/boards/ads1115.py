import time
import threading
import logging
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS

# Constants
NUMBER_OF_READINGS = 100
ADS_PIN_NUMBERS = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
FAST_DATA_RATE = 860
DATA_RATE = 128  # Set the desired data rate in samples per second (SPS)
BREATH_BETWEEN_READINGS = 1.0 / DATA_RATE  # Calculate the sleep time between readings based on the data rate

logger = logging.getLogger(__name__)

class ADS1115:
    def __init__(self, ads, board_config):
        self.ads = ads
        self.board_id = board_config['id']
        self.i2c_address = board_config['i2c_address']
        self.label = board_config.get('label', 'Unknown')
        self.location = board_config.get('location', 'Unknown')
        self.purpose = board_config.get('purpose', 'Unknown')
        self.readings = {pin: [] for pin in range(4)}  # Dictionary to store readings for each pin
        self.readingsfull = False
        self.lock = threading.Lock()
        self._stop_thread = threading.Event()
        # Set the data rate for initial readings
        self.ads.data_rate = FAST_DATA_RATE
        self.get_startup_readings()
        self.ads.data_rate = DATA_RATE
        self.thread = threading.Thread(target=self.poll_pins)
        logger.info(f"     🔮 Initialized ADS1115 at address {self.i2c_address} and board ID {self.board_id} ({self.label}, {self.location}, {self.purpose})")
        self.thread.start()

    def get_startup_readings(self):
        """Get initial readings to ensure that the readings list is populated."""
        while not self.readingsfull:
            for pin in range(4):
                try:
                    reading = AnalogIn(self.ads, ADS_PIN_NUMBERS[pin]).voltage
                    with self.lock:
                        self.readings[pin].append(reading)

                except Exception as e:
                    logger.error(f"💢 Error reading from ADS1115 on board {self.board_id}, pin {pin}: {e}")
            if len(self.readings[pin]) > NUMBER_OF_READINGS:
                if not self.readingsfull:
                    self.readingsfull = True
                    
    def poll_pins(self):
        """Poll all pins on the ADS1115 and maintain a running tally of the readings."""
        while not self._stop_thread.is_set():
            for pin in range(4):
                try:
                    reading = AnalogIn(self.ads, ADS_PIN_NUMBERS[pin]).voltage
                    with self.lock:
                        self.readings[pin].append(reading)
                        if len(self.readings[pin]) > NUMBER_OF_READINGS:             
                            self.readings[pin].pop(0)
                    # logger.debug(f"     🌟 Board {self.board_id}, Pin {pin}: {reading:.6f} V")
                except Exception as e:
                    logger.error(f"💢 Error reading from ADS1115 on board {self.board_id}, pin {pin}: {e}")
            time.sleep(BREATH_BETWEEN_READINGS)  # Adjust the sleep time based on the data rate

    def get_readings(self, pin):
        """Retrieve the latest readings for a specific pin."""
        with self.lock:
            return self.readings.get(pin, [])

    def stop(self):
        """Stop the polling thread."""
        self._stop_thread.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            logger.warning(f"ADConverter polling thread for board {self.board_id} did not stop within the timeout period.")

# Example usage
if __name__ == "__main__":
    import board
    import busio

    logging.basicConfig(level=logging.DEBUG)

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=0x48)

    # Example board configuration
    board_config = {
        "type": "ADS1115",
        "id": "master_control_ad_converter",
        "label": "Voltage Detector - Master Control",
        "location": "Master Control",
        "i2c_address": "0x48",
        "purpose": "Voltage Sensing"
    }

    ad_converter = ADS1115(ads, board_config)

    try:
        while True:
            time.sleep(1)
            # Just for demonstration, print out the readings
            for pin in range(4):
                readings = ad_converter.get_readings(pin)
                logger.info(f"Pin {pin} readings: {readings}")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    finally:
        ad_converter.stop()
        logger.info("AD Converter stopped.")
