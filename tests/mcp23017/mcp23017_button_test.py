import time
import board
import busio
from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017

# Set up I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Create MCP23017 instance at address 0x20
mcp = MCP23017(i2c, address=0x20)

# Set up button on pin 0
button = mcp.get_pin(0)
button.direction = Direction.INPUT
button.pull = Pull.UP

# Initialize the button state
button_state = False  # False = off, True = on
last_button_read = button.value
print(f"Initial button state: {'off' if not button_state else 'on'}")

while True:
    # Read the button state
    current_read = button.value

    # Check if the button has been pressed (transition from high to low)
    if last_button_read and not current_read:
        # Toggle the button state
        button_state = not button_state
        state_str = "off" if not button_state else "on"
        print(f"Button is now {state_str}")

    # Update the last button read
    last_button_read = current_read

    # Small delay to debounce
    time.sleep(0.1)
