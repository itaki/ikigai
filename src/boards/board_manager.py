from boards.mcp23017 import MCP23017
from boards.pca9685 import PCA9685
from boards.ads1115 import ADS1115
from loguru import logger
import busio
import board

class BoardManager:
    def __init__(self, i2c):
        self.i2c = i2c  # Pass the I2C interface to the class
        self.boards = {}

    def initialize_board(self, board_config):
        """Initialize a board based on its type and full configuration."""
        board_type = board_config.get('type')
        label = board_config.get('label')

        try:
            if board_type == "MCP23017":
                board = MCP23017(self.i2c, board_config)  # Pass the entire config to your MCP23017 class
            elif board_type == "PCA9685":
                board = PCA9685(self.i2c, board_config)  # Pass the entire config to your PCA9685 class
            elif board_type == "ADS1115":
                board = ADS1115(self.i2c, board_config)  # Pass the entire config to your ADS1115 class
            else:
                logger.error(f"❌ Unknown board type '{board_type}' for board '{label}'")
                return None

            # Log success
            logger.success(f"✅ Board '{label}' initialized successfully.")
            return board

        except Exception as e:
            logger.error(f"💢 Failed to initialize board '{label}': {str(e)}")
            return None

    def initialize_all_boards(self, boards_config):
        """Initialize all boards from the provided configuration."""
        for board_config in boards_config:
            board = self.initialize_board(board_config)
            if board:
                self.boards[board_config['id']] = board
        logger.success("🎉 All boards initialized successfully.")

    def get_board(self, board_id):
        """Get a specific board by its ID."""
        return self.boards.get(board_id)
