from utils.config_loader import ConfigLoader
from board_manager import BoardManager  # Import the new BoardManager class
from loguru import logger
import busio
import board

# Configure Loguru logger
logger.add("logs/shop_manager.log", rotation="1 MB")  # Save logs to a file, rotate when file size exceeds 1 MB

def main():
    try:
        logger.info("🔧 Starting the shop management application...")

        # Initialize the configuration loader
        config_loader = ConfigLoader()
        config_loader.reload_configs()

        # Retrieve the boards configuration
        boards_config = config_loader.get_boards()

        # Set up I2C interface
        i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize the BoardManager with I2C
        board_manager = BoardManager(i2c)

        # Initialize all boards
        board_manager.initialize_all_boards(boards_config)

        # Application logic can be added here, using the initialized boards from the board_manager

    except Exception as e:
        logger.error(f"💢 An error occurred in the shop management application: {str(e)}")

if __name__ == "__main__":
    main()
