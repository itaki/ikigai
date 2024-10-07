import logging
import RPi.GPIO as GPIO
import time

logger = logging.getLogger(__name__)

class Relay:
    def __init__(self, config):
        self.label = config.get('label', 'Unknown Collector')
        self.board_id = config['connection']['board']
        self.pin = config['connection']['pins'][0]
        self.state = "off"


        logger.info(f"💡     Relay '{self.label}' initialized on board {self.board_id}, pin {self.pin}")

    def turn_on(self):
        if self.state != "on":
            self.state = "on"
            GPIO.output(self.pin, GPIO.HIGH)
            logger.debug(f"💡    Relay '{self.label}' turned on")

    def turn_off(self):
        if self.state != "off":
            self.state = "off"
            GPIO.output(self.pin, GPIO.LOW)
            logger.debug(f"💡    Relay '{self.label}' turned off")

    def get_state(self):
        return self.state

