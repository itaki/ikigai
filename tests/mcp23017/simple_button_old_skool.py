import os
import sys
import time
import threading

# Add the parent directory of the current file to the system path
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
sys.path.append(parent_dir)

import board
import busio
import logging
from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration for buttons
button_configs = [
    {
        "label": "Hose Button",
        "id": "hose_button",
        "physical_location": "By the Hose",
        "connection": {
            "hub": "main-hub",
            "address": "0x20",
            "pin": 0
        }
    },
    {
        "label": "LEFT Miter Saw Button",
        "id": "left_miter_saw_button",
        "physical_location": "Above the miter saw",
        "connection": {
            "hub": "main-hub",
            "address": "0x20",
            "pin": 1
        }
    },
    {
        "label": "RIGHT Miter Saw Button",
        "id": "right_miter_saw_button",
        "physical_location": "Above the miter saw",
        "connection": {
            "hub": "main-hub",
            "address": "0x20",
            "pin": 2
        }
    },
    {
        "label": "Test Button",
        "id": "test_button",
        "physical_location": "Test Location",
        "connection": {
            "hub": "main-hub",
            "address": "0x20",
            "pin": 3
        }
    }
]

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize MCP23017
mcp = MCP23017(i2c, address=int(button_configs[0]['connection']['address'], 16))

# Initialize buttons
buttons = []
for config in button_configs:
    try:
        pin = config['connection']['pin']
        button = mcp.get_pin(pin)
        button.direction = Direction.INPUT
        button.pull = Pull.UP
        buttons.append((config['label'], button))
        logger.debug(f"      🚥 🔵 Button {config['label']} initialized at pin {pin}")
    except Exception as e:
        logger.error(f"💢 Error initializing button {config['label']}: {e}")

def poll_buttons():
    while True:
        for label, button in buttons:
            if not button.value:  # Button press detected
                logger.debug(f"      🚥 🔵 Button {label} pressed")
                print(f"Button {label} pressed")
                time.sleep(0.5)  # Debounce delay
        time.sleep(0.1)  # Small delay to avoid busy-waiting

# Start polling in a background thread
polling_thread = threading.Thread(target=poll_buttons, daemon=True)
polling_thread.start()

try:
    while True:
        # Main program can run other tasks here
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Program interrupted by user")
