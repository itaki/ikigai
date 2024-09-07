import time
import board
import busio
from adafruit_pca9685 import PCA9685

# Set up I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Create PCA9685 instance at address 0x42
pca = PCA9685(i2c, address=0x42)
pca.frequency = 1000  # Set frequency to 1000 Hz for LED control

# Set up RGB LED on pins 13, 14, 15
led_red = pca.channels[13]
led_green = pca.channels[14]
led_blue = pca.channels[15]

# Function to set the LED to a specific color
def set_led_color(red, green, blue):
    # Correct logic for common anode RGB LED
    led_red.duty_cycle = red
    led_green.duty_cycle = green
    led_blue.duty_cycle = blue

# Test colors
colors = {
    "red": (0, 0xFFFF, 0xFFFF),       # Turn on red (turn off green and blue)
    "green": (0xFFFF, 0, 0xFFFF),     # Turn on green (turn off red and blue)
    "blue": (0xFFFF, 0xFFFF, 0),      # Turn on blue (turn off red and green)
    "yellow": (0, 0, 0xFFFF),         # Turn on red and green (turn off blue)
    "cyan": (0xFFFF, 0, 0),           # Turn on green and blue (turn off red)
    "magenta": (0, 0xFFFF, 0),        # Turn on red and blue (turn off green)
    "white": (0, 0, 0),               # Turn on all colors
    "off": (0xFFFF, 0xFFFF, 0xFFFF),  # Turn off all colors
}

while True:
    for color_name, (red, green, blue) in colors.items():
        print(f"Setting LED to {color_name}")
        set_led_color(red, green, blue)
        time.sleep(1)
