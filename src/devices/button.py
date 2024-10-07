import logging
from loguru import logger
from digitalio import DigitalInOut, Direction, Pull


class Button:
    def __init__(self, config, board):
        self.label = config['label']
        self.id = config['id']
        self.pin_number = config['connection']['pin']
        self.board = board
        self.state = 'off'
        self.is_pressed = False
        self.error_logged = False

        self.pin = None
        self.setup_pin()


    def setup_pin(self):
        try:
            self.pin = self.board.get_pin(self.pin_number)
            self.pin.direction = Direction.INPUT
            self.pin.pull = Pull.UP
            logger.info(f"✅ 🔘 Button {self.label} initialized on pin {self.pin_number}")
        except AttributeError as e:
            logger.error(f"💢 🔘 Board for button {self.label} does not support required methods: {e}")
        except Exception as e:
            logger.error(f"💢 🔘 Error setting up pin {self.pin_number} for button {self.label}: {e}")

    def read_pin(self):
        try:
            if self.pin:
                return not self.pin.value  # Invert because we're using pull-up resistors
            else:
                if not self.error_logged:
                    logger.error(f"💢 🔘 Pin not set up for button {self.label}")
                    self.error_logged = True
                return None
        except Exception as e:
            if not self.error_logged:
                logger.error(f"💢 🔘 Error reading pin {self.pin_number} for button {self.label}: {e}")
                self.error_logged = True
            return None

    def get_state(self):
        return self.state

    def update_state(self):
        pin_state = self.read_pin()
        if pin_state is not None:
            new_state = 'pressed' if pin_state else 'released'
            if new_state != self.state:
                self.state = new_state
                logger.info(f"🔘 Button {self.label} state changed to: {self.state}")

    def cleanup(self):
        logger.debug(f"🧹 🔘 Cleaning up Button {self.label}")
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
        logger.debug(f"🔘 Button status: {status}")

    # Instantiate and set up the button
    button = Button(config=button_config, board=mcp, status_callback=status_callback)

    # Main loop to simulate the button press
    try:
        while True:
            button.check_status()
            time.sleep(0.1)
    except KeyboardInterrupt:
        button.cleanup()