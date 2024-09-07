from loguru import logger
import RPi.GPIO as GPIO
import time

class DustCollector:
    def __init__(self, config):
        self.label = config.get('label', 'Unknown Collector')
        self.pin = config['connection']['pins'][0]
        self.spin_up_delay = config['preferences'].get('spin_up_delay', 5)
        self.minimum_up_time = config['preferences'].get('minimum_up_time', 10)
        self.cool_down_time = config['preferences'].get('cool_down_time', 30)
        self.relay_status = "off"
        self.last_on_time = 0
        self.last_off_time = time.time()

        # Setup GPIO for relay
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)

        logger.info(f"🌀 Dust Collector '{self.label}' initialized on Raspberry Pi GPIO pin {self.pin}")

    def turn_on(self):
        if self.relay_status != "on":
            self.relay_status = "on"
            GPIO.output(self.pin, GPIO.HIGH)
            self.last_on_time = time.time()
            logger.debug(f"🌀 Dust Collector '{self.label}' turned on")
            time.sleep(self.spin_up_delay)

    def turn_off(self):
        if self.relay_status != "off":
            self.relay_status = "off"
            GPIO.output(self.pin, GPIO.LOW)
            self.last_off_time = time.time()
            logger.debug(f"🌀 Dust Collector '{self.label}' turned off")

    def spindown(self):
        # Implement spindown routine if needed
        pass

    def cleanup(self):
        GPIO.cleanup(self.pin)
        logger.debug(f"🌀 Dust Collector '{self.label}' GPIO cleaned up")

