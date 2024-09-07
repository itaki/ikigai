# tools/vs_board_test.py

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from loguru import logger
import sys

# Add the src directory to the Python path
sys.path.append('./src')

# Import the ConfigLoader
from utils.config_loader import ConfigLoader

# Configure Loguru logger
logger.add("logs/vs_board_test.log", rotation="1 MB")

def setup_board(board_config):
    try:
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create the ADC object using the I2C bus
        ads = ADS.ADS1115(i2c, address=int(board_config['i2c_address'], 16))
        
        logger.info(f"Successfully initialized ADS1115 at address {board_config['i2c_address']}")
        return ads
    except Exception as e:
        logger.error(f"Failed to initialize ADS1115: {str(e)}")
        return None

def read_channels(ads):
    channels = []
    for i in range(4):
        chan = AnalogIn(ads, getattr(ADS, f'P{i}'))
        channels.append(chan)
    return channels

def main():
    # Load configurations
    config_loader = ConfigLoader()
    config_loader.reload_configs()
    boards = config_loader.get_boards()
    
    # Find the ADS1115 board in the configuration
    ads1115_config = next((board for board in boards if board['type'] == 'ADS1115'), None)
    
    if not ads1115_config:
        logger.error("No ADS1115 board found in configuration")
        return

    logger.info(f"Found ADS1115 configuration: {ads1115_config}")

    ads = setup_board(ads1115_config)
    if not ads:
        logger.error("Failed to set up the board. Exiting.")
        return

    channels = read_channels(ads)
    
    try:
        while True:
            for i, chan in enumerate(channels):
                voltage = chan.voltage
                logger.info(f"Channel {i}: {voltage:.6f} V")
            logger.info("---")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Test stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred during reading: {str(e)}")

if __name__ == "__main__":
    main()
