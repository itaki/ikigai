import adafruit_mcp230xx.mcp23017 as MCP
import board
import busio
from digitalio import Direction, Pull

class MCP23017:
    def __init__(self, i2c, config):
        self.mcp = MCP.MCP23017(i2c, address=int(config['i2c_address'], 16))
        self.label = config.get('label', 'Unknown')
        self.pins = {}

    def setup_input(self, pin):
        """Set up a pin as an input."""
        self.pins[pin] = self.mcp.get_pin(pin)
        self.pins[pin].direction = Direction.INPUT
        self.pins[pin].pull = Pull.UP  # Assuming you want to use a pull-up resistor

    def setup_output(self, pin):
        """Set up a pin as an output."""
        self.pins[pin] = self.mcp.get_pin(pin)
        self.pins[pin].direction = Direction.OUTPUT
        self.pins[pin].value = False  # Initialize the pin to LOW

    def read_input(self, pin):
        """Read the value from an input pin."""
        return self.pins[pin].value

    def write_output(self, pin, value):
        """Write a value to an output pin."""
        self.pins[pin].value = value

