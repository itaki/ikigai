import logging
import RPi.GPIO as GPIO
import time

logger = logging.getLogger(__name__)

class Relay:
    def __init__(self, config):
        self.label = config.get('label', 'Unknown Collector')
        self.board_id = config['connection']['board']
        self.pin = config['connection']['pins'][0]
        self.relay_status = "off"


        logger.info(f"💡     Relay '{self.label}' initialized on board {self.board_id}, pin {self.pin}")

    def turn_on(self):
        if self.relay_status != "on":
            self.relay_status = "on"
            GPIO.output(self.pin, GPIO.HIGH)
            logger.debug(f"💡    Relay '{self.label}' turned on")

    def turn_off(self):
        if self.relay_status != "off":
            self.relay_status = "off"
            GPIO.output(self.pin, GPIO.LOW)
            logger.debug(f"💡    Relay '{self.label}' turned off")

