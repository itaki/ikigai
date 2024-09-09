from boards.mcp23017 import MCP23017
from boards.pca9685 import PCA9685
from boards.ads1115 import ADS1115
from loguru import logger
import smbus2

class BoardManager:
    def __init__(self, i2c):
        self.i2c = i2c
        self.boards = {}
        logger.info("🔧 BoardManager initialized with I2C interface")

    def is_device_present(self, address):
        """Check if a device is present at the given I2C address."""
        try:
            smbus2.SMBus(1).read_byte(address)
            return True
        except Exception as e:
            return False

    def initialize_board(self, board_config, app_config):
        use_boards = app_config.get('USE_BOARDS', {})
        board_type = board_config.get('type')
        label = board_config.get('label')
        address = int(board_config['i2c_address'], 16)

        if not self.is_device_present(address):
            logger.warning(f"❌ No device found at I2C address {hex(address)} for board '{label}'")
            return None

        try:
            if board_type == "MCP23017" and use_boards.get("USE_MCP23017", False):
                board = MCP23017(self.i2c, board_config, app_config)
            elif board_type == "PCA9685" and use_boards.get("USE_PCA9685", False):
                board = PCA9685(self.i2c, board_config, app_config)
            elif board_type == "ADS1115" and use_boards.get("USE_ADS1115", False):
                board = ADS1115(self.i2c, board_config, app_config)
            else:
                logger.error(f"❌ Unknown or disabled board type '{board_type}' for board '{label}'")
                return None

            return board

        except Exception as e:
            logger.error(f"💥 Failed to initialize board '{label}': {str(e)}")
            return None

    def initialize_all_boards(self, boards_config, app_config):
        for board_id, board_config in boards_config.items():
            board_type = board_config.get('type')
            use_key = f"USE_{board_type.upper()}"
            if app_config.get('USE_BOARDS', {}).get(use_key, False):
                board = self.initialize_board(board_config, app_config)
                if board:
                    self.boards[board_id] = board

        return self.boards

    def get_board(self, board_id):
        return self.boards.get(board_id)

    def get_boards(self):
        return self.boards

    def cleanup(self):
        logger.info("🧹 Cleaning up BoardManager")
        for board_id, board in self.boards.items():
            if hasattr(board, 'cleanup'):
                try:
                    board.cleanup()
                    logger.info(f"✅ Board {board_id} cleaned up successfully")
                except Exception as e:
                    logger.error(f"💥 Error cleaning up board {board_id}: {str(e)}")
        logger.info("✅ BoardManager cleanup completed")
