import RPi.GPIO as GPIO
import time

# Set up the GPIO mode
GPIO.setmode(GPIO.BOARD)  # Use BOARD pin numbering

# Set up GPIO pin 40 as an output pin
GPIO.setup(40, GPIO.OUT)

# Turn on the pin (set it HIGH)
GPIO.output(40, GPIO.HIGH)

# Keep the pin on for 5 seconds
time.sleep(5)

# Clean up the GPIO settings
GPIO.cleanup()