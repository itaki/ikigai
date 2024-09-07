import logging
from loguru import logger
from digitalio import DigitalInOut, Direction, Pull

logger = logging.getLogger(__name__)

class Button:
    def __init__(self, config, board):
        self.label = config['label']
        self.id = config['id']
        self.pin_number = config['connection']['pin']
        self.board = board
        self.state = 'off'
        self.is_pressed = False
        self.error_logged = False
        logger.debug(f"Button {self.label} initialized on pin {self.pin_number}")
        self.pin = None
        self.setup_pin()


    def setup_pin(self):
        try:
            logger.debug(f"Attempting to get pin {self.pin_number} from board")
            self.pin = self.board.get_pin(self.pin_number)
            logger.debug(f"Successfully got pin {self.pin_number}")
            self.pin.direction = Direction.INPUT
            logger.debug(f"Set direction to INPUT for pin {self.pin_number}")
            self.pin.pull = Pull.UP
            logger.debug(f"Set pull-up for pin {self.pin_number}")
            logger.debug(f"Button '{self.label}' pin setup complete on pin {self.pin_number}")
        except AttributeError as e:
            logger.error(f"Board for button {self.label} does not support required methods: {e}")
        except Exception as e:
            logger.error(f"Error setting up pin {self.pin_number} for button {self.label}: {e}")

    def read_pin(self):
        try:
            if self.pin:
                return not self.pin.value  # Invert because we're using pull-up resistors
            else:
                if error_logged is False:
                    logger.error(f"Pin not set up for button {self.label}")
                    error_logged = True
                return None
        except Exception as e:
            if self.error_logged is False:
                logger.error(f"Error reading pin {self.pin_number} for button {self.label}: {e}")
                self.error_logged = True
            return None

    def cleanup(self):
        logger.debug(f"Cleaning up Button {self.label}")
        # No specific cleanup needed for MCP23017 buttons

# For testing, you can add a main function to instantiate and run this button class
if __name__ == "__main__":
    import board
    import busio
    from adafruit_mcp230xx.mcp23017 import MCP23017
    import time

    logging.basicConfig(level=logging.DEBUG)

    # I2C setup
    i2c = busio.I2C(board.SCL, board.SDA)

    # MCP23017 setup
    mcp = MCP23017(i2c)

    # Button configuration
    button_config = {
        "label": "Test Button",
        "connection": {
            "pin": 0  # Pin 0 on MCP23017
        }
    }

    # Status callback
    def status_callback(status):
        logger.debug(f"Button status: {status}")

    # Instantiate and set up the button
    button = Button(config=button_config, board=mcp, status_callback=status_callback)

    # Main loop to simulate the button press
    try:
        while True:
            button.check_status()
            time.sleep(0.1)
    except KeyboardInterrupt:
        button.cleanup()
