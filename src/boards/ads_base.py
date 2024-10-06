import time
import threading
from loguru import logger
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS1115_MODULE
import adafruit_ads1x15.ads1015 as ADS1015_MODULE

ADS1115_PIN_NUMBERS = {0: ADS1115_MODULE.P0, 1: ADS1115_MODULE.P1, 2: ADS1115_MODULE.P2, 3: ADS1115_MODULE.P3}
ADS1015_PIN_NUMBERS = {0: ADS1015_MODULE.P0, 1: ADS1015_MODULE.P1, 2: ADS1015_MODULE.P2, 3: ADS1015_MODULE.P3}

class ADSBase:
    def __init__(self, i2c, config, app_config):
        self.i2c = i2c
        self.board_id = config['id']
        self.i2c_address = int(config['i2c_address'], 16)
        self.label = config.get('label', 'Unknown')
        self.location = config.get('location', 'Unknown')
        self.purpose = config.get('purpose', 'Unknown')
        self.readings = {pin: [] for pin in range(4)}
        self.is_initialized = False
        self.lock = threading.Lock()
        self._stop_thread = threading.Event()

        self.ads = self._initialize_ads()
        self._configure_settings(app_config)
        
        self.thread = threading.Thread(target=self.poll_pins)
        self.thread.start()

    def _initialize_ads(self):
        raise NotImplementedError("Subclasses must implement this method")

    def _configure_settings(self, app_config):
        raise NotImplementedError("Subclasses must implement this method")

    def read_pins(self):
        self.ads.data_rate = self.data_rate
        logger.info(f"🔄 Polling {self.__class__.__name__} {self.label} at {self.data_rate} SPS")
        while not self._stop_thread.is_set():
            for pin in range(4):
                try:
                    reading = AnalogIn(self.ads, self.PIN_NUMBERS[pin]).voltage
                    with self.lock:
                        self.readings[pin].append(reading)
                        if len(self.readings[pin]) > self.max_readings:
                            self.readings[pin].pop(0)
                except Exception as e:
                    logger.error(f"Error reading pin {pin} on {self.__class__.__name__} {self.label}: {e}")
            
            if not self.is_initialized and all(len(readings) >= self.max_readings for readings in self.readings.values()):
                self.is_initialized = True
                logger.info(f"✅ {self.__class__.__name__} {self.label} initialized with {self.max_readings} readings per pin")
            
            time.sleep(1.0 / self.data_rate)

    def poll_pins(self):
        try:
            self.read_pins()
        except Exception as e:
            logger.error(f"💢 Error during polling: {e}")

    def get_readings(self, pin):
        with self.lock:
            return list(self.readings[pin])

    def stop(self):
        logger.info(f"🛑 Stopping {self.__class__.__name__} polling thread")
        self._stop_thread.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            logger.warning(f"⚠️ ADConverter polling thread for board {self.board_id} did not stop within the timeout period.")
        else:
            logger.info(f"✅ ADConverter polling thread for board {self.board_id} stopped successfully.")

    def cleanup(self):
        logger.info(f"Cleaning up {self.__class__.__name__} board {self.board_id}")
        self.stop()

class ADS1115(ADSBase):
    PIN_NUMBERS = ADS1115_PIN_NUMBERS

    def _initialize_ads(self):
        try:
            ads = ADS1115_MODULE.ADS1115(self.i2c, address=self.i2c_address)
            logger.info(f"🔮 Initialized ADS1115 {self.label} at {hex(self.i2c_address)}")
            return ads
        except Exception as e:
            logger.error(f"💢 Failed to initialize ADS1115 {self.label} at address {hex(self.i2c_address)}: {str(e)}")
            raise e

    def _configure_settings(self, app_config):
        settings = app_config['ADS1115_SETTINGS']
        self.data_rate = settings['NORMAL_DATA_RATE']
        self.max_readings = settings['MAX_READINGS']

class ADS1015(ADSBase):
    PIN_NUMBERS = ADS1015_PIN_NUMBERS

    def _initialize_ads(self):
        try:
            ads = ADS1015_MODULE.ADS1015(self.i2c, address=self.i2c_address)
            logger.info(f"🔮 Initialized ADS1015 {self.label} at {hex(self.i2c_address)}")
            return ads
        except Exception as e:
            logger.error(f"💢 Failed to initialize ADS1015 {self.label} at address {hex(self.i2c_address)}: {str(e)}")
            raise e

    def _configure_settings(self, app_config):
        settings = app_config['ADS1015_SETTINGS']
        self.data_rate = settings['NORMAL_DATA_RATE']
        self.max_readings = settings['MAX_READINGS']