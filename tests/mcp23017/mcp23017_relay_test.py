import time
import board
import busio
import adafruit_mcp230xx.mcp23017 as MCP
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the MCP23017 I2C address and pin
MCP23017_ADDRESS = 0x20
PIN = 2  # Pin 2 on the MCP23017

def setup_mcp():
    i2c = busio.I2C(board.SCL, board.SDA)
    mcp = MCP.MCP23017(i2c, address=MCP23017_ADDRESS)
    pin = mcp.get_pin(PIN)
    pin.switch_to_output(value=False)
    logger.debug(f"      🚥 MCP23017 at address {MCP23017_ADDRESS} set up. Pin {PIN} configured as output.")
    return pin

def toggle_pin(pin):
    new_state = not pin.value
    pin.value = new_state
    state_str = "on" if new_state else "off"
    logger.info(f"     🔮 Pin {PIN} toggled {state_str}.")

def main():
    pin = setup_mcp()
    try:
        while True:
            toggle_pin(pin)
            time.sleep(0.5)  # Wait for half a second
    except KeyboardInterrupt:
        logger.info("Shutting down due to keyboard interrupt.")
    except Exception as e:
        logger.error(f"💢 Unexpected error: {e}")
    finally:
        pin.value = False  # Ensure the pin is turned off on exit
        logger.info("Clean shutdown complete.")

if __name__ == "__main__":
    main()
