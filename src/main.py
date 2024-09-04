from utils.config_loader import ConfigLoader
from boards.board_manager import BoardManager
from gui.main_window import MainWindow  # Import the main window for the GUI
from loguru import logger
import busio
import board
import sys
from PyQt6.QtWidgets import QApplication

# Configuration flags
USE_GUI = False
USE_AD_CONVERTERS = False
USE_BUTTONS = True
USE_SERVOS = True 
USE_RGB_LEDS = True

use_boards = {
    "USE_AD_CONVERTERS": USE_AD_CONVERTERS,
    "USE_BUTTONS": USE_BUTTONS,
    "USE_SERVOS": USE_SERVOS,
    "USE_RGB_LEDS": USE_RGB_LEDS
}   

# Configure Loguru logger
logger.add("logs/shop_manager.log", rotation="1 MB")

def main():
    try:
        logger.info("🔧 Starting the shop management application...")

        # Load configuration
        config_loader = ConfigLoader()
        config_loader.reload_configs()

        # Initialize I2C interface
        i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize the board manager
        board_manager = BoardManager(i2c)
        boards_config = config_loader.get_boards()
        board_manager.initialize_all_boards(boards_config, use_boards)

        if USE_GUI:
            # Initialize the GUI
            app = QApplication(sys.argv)
            window = MainWindow(board_manager)  # Pass the BoardManager to the GUI
            window.show()

        # Start the GUI event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"💢 An error occurred in the shop management application: {str(e)}")

if __name__ == "__main__":
    main()
