from loguru import logger
import busio
import board
import time
from utils.config_loader import ConfigLoader
from managers.board_manager import BoardManager
from managers.device_manager import DeviceManager
from managers.style_manager import StyleManager
from gui.main_window import MainWindow

# Configure Loguru logger
logger.add("logs/shop_manager.log", rotation="1 MB")

# Load configurations
config_loader = ConfigLoader()
config_loader.reload_configs()
app_config = config_loader.get_app_config()

# Extract configuration values
USE_GUI = app_config.get('USE_GUI', False)
USE_BOARDS = app_config.get('USE_BOARDS', {})
USE_DEVICES = app_config.get('USE_DEVICES', {})

def initialize_gui(board_manager, device_manager):
    if USE_GUI:
        from gui.main_window import MainWindow
        from gui.app_state import AppState
        from PyQt6.QtWidgets import QApplication
        logger.info("🖥️ Initializing GUI")
        app = QApplication([])
        logger.info("🖥️ QApplication initialized")
        app_state = AppState(board_manager, device_manager)
        logger.info("🖥️ AppState initialized")
        main_window = MainWindow(app_state)
        logger.info("🖥️ MainWindow initialized")
        return app, main_window
    return None, None

def initialize_managers(i2c):
    boards_config = config_loader.get_boards()
    devices_config = config_loader.get_devices()
    gates_config = config_loader.get_gates()

    if isinstance(boards_config, list):
        boards_config = {board['id']: board for board in boards_config}

    board_manager = BoardManager(i2c)
    boards = board_manager.initialize_all_boards(boards_config, app_config)

    style_manager = StyleManager()
    rgbled_styles = style_manager.get_styles()

    device_manager = DeviceManager(devices_config, gates_config, boards, rgbled_styles, app_config)
    logger.info("🔧 Managers initialized: BoardManager, StyleManager, DeviceManager")
    
    return board_manager, device_manager

def main():
    device_manager = None
    board_manager = None
    try:
        logger.info("🚀 Starting the shop management application...")
        
        i2c = busio.I2C(board.SCL, board.SDA)
        logger.info("🔌 I2C interface initialized")

        board_manager, device_manager = initialize_managers(i2c)
        logger.info("🔧 Managers initialized: BoardManager, DeviceManager")

        app, main_window = initialize_gui(board_manager, device_manager)
        logger.info("🖥️ GUI initialized")

        if USE_GUI:
            main_window.show()
            app.exec()
        else:
            # Main application loop for non-GUI mode
            while True:
                try:
                    device_manager.update()
                    time.sleep(0.1)  # Adjust as needed to control loop speed
                except Exception as e:
                    logger.error(f"💥 An error occurred during device update: {str(e)}")
                    break  # Exit the loop on error

    except KeyboardInterrupt:
        logger.info("🛑 Program interrupted by user")
    except Exception as e:
        logger.error(f"💥 An error occurred in the shop management application: {str(e)}")
    finally:
        if device_manager:
            device_manager.cleanup()
        if board_manager:
            board_manager.cleanup()
        logger.info("🧹 All threads and resources cleaned up gracefully.")

if __name__ == "__main__":
    main()
