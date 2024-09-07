import json
import os
import time
import logging
import board
import busio
import sys
from adafruit_pca9685 import PCA9685 as Adafruit_PCA9685
import keyboard  # Make sure to install this package with `pip install keyboard`
import RPi.GPIO as GPIO

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the configuration files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
GATES_FILE = os.path.join(BASE_DIR, 'gates.json')

if not os.path.exists(CONFIG_FILE) or not os.path.exists(GATES_FILE):
    logger.error(f"💢 Configuration or gates file not found. Exiting.")
    sys.exit(1)

with open(CONFIG_FILE, 'r') as config_file:
    config = json.load(config_file)

with open(GATES_FILE, 'r') as gates_file:
    gates = json.load(gates_file)["gates"]

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize boards
boards = {}  # Dictionary to store initialized boards
for board_config in config.get('boards', []):
    board_type = board_config['type']
    board_id = board_config['id']
    purpose = board_config.get('purpose', 'LED Control')  # Default to LED Control if not specified

    try:
        # Check if the board's purpose is Servo Control
        if purpose == 'Servo Control':
            if board_type == 'PCA9685':
                boards[board_id] = Adafruit_PCA9685(i2c, address=int(board_config['i2c_address'], 16))
                logger.info(f"     🔮 Initialized PCA9685 {board_config['label']} at address {board_config['i2c_address']} for Servo Control")
            # Add other board types if needed
        else:
            logger.info(f"     🔮 Skipping initialization of {board_id} as it is set to {purpose}")
    except Exception as e:
        logger.error(f"💢 Failed to initialize board {board_config.get('label', 'unknown')}: {e}")

# Continue with the rest of your script
# Function to set servo angle
def calculate_duty_cycle(angle, min_pulse_width=1.0, max_pulse_width=2.0, frequency=50):
    # Period of the PWM signal (in milliseconds)
    period = 1000.0 / frequency  # 20 ms for 50 Hz

    # Calculate the pulse width in milliseconds
    pulse_width = min_pulse_width + (angle / 180.0) * (max_pulse_width - min_pulse_width)

    # Convert the pulse width to a duty cycle value (0-65535)
    duty_cycle = int((pulse_width / period) * 65535)

    return duty_cycle

# Servo test function
def servo_test():
    try:
        for gate_name, gate_info in gates.items():
            board_id = gate_info['io_location']['board']
            pin = gate_info['io_location']['pin']
            min_angle = gate_info['min']
            max_angle = gate_info['max']

            if board_id not in boards:
                logger.error(f"💢 Board {board_id} not initialized. Skipping gate {gate_name}.")
                continue

            pca = boards[board_id]

            logger.info(f"     🔮 Testing gate: {gate_name}")
            logger.info(f"     🔮 Physical Location: {gate_info['physical_location']}")
            logger.info(f"     🔮 Pin: {pin}")
            logger.info(f"     🔮 Min Angle: {min_angle}, Max Angle: {max_angle}")

            while True:
                # Move servo from min to max
                pca.channels[pin].duty_cycle = calculate_duty_cycle(min_angle) # Convert angle to PWM duty cycle
                time.sleep(0.5)

                # Move servo from max to min
                pca.channels[pin].duty_cycle = calculate_duty_cycle(max_angle)  # Convert angle to PWM duty cycle
                time.sleep(0.5)

                # Check for keypress
                if keyboard.is_pressed('esc'):
                    logger.info("Exiting servo test.")
                    return
                elif keyboard.is_pressed('space'):
                    # Stop the servo
                    pca.channels[pin].duty_cycle = 0
                    logger.info(f"     🔮 Stopped gate {gate_name}")
                    break

    except KeyboardInterrupt:
        logger.info("Servo test interrupted by user.")
    finally:
        # Cleanup
        GPIO.cleanup()
        logger.info("GPIO cleanup complete.")

# Run the servo test
if __name__ == "__main__":
    servo_test()
