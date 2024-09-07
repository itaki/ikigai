import board
import busio
from adafruit_pca9685 import PCA9685
import time

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Define the PCA9685 board configuration
i2c_address = 0x40  # I2C address for the PCA9685
frequency = 1000  # Frequency for LED control

# Initialize the PCA9685 board
pwm_led = PCA9685(i2c, address=i2c_address)
pwm_led.frequency = frequency

# Define the pins for the RGB LED
red_pin = 3
green_pin = 4
blue_pin = 5

# Set the LED to purple (Red and Blue ON, Green OFF)
pwm_led.channels[red_pin].duty_cycle = 0x4444  # 50% brightness for Red
pwm_led.channels[green_pin].duty_cycle = 0x4444  # Green OFF
pwm_led.channels[blue_pin].duty_cycle = 0x4444  # 50% brightness for Blue

print("Hose LED set to purple.")
time.sleep(10)
# Cleanup
pwm_led.deinit()
