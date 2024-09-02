from utils.config_loader import ConfigLoader
import logging

# Initialize the logger
logger = logging.getLogger("shop_logger")

def main():
    try:
        # Initialize the configuration loader
        config_loader = ConfigLoader()

        # Load the configurations
        config_loader.reload_configs()

        # Retrieve configurations
        boards = config_loader.get_boards()
        tools = config_loader.get_tools()
        gates = config_loader.get_gates()

        # Log the loaded configurations
        logger.debug(f"Boards: {boards}")
        logger.debug(f"Tools: {tools}")
        logger.debug(f"Gates: {gates}")

        # Application logic can be added here
        # For example: Initialize managers, set up devices, start main loop, etc.

    except Exception as e:
        logger.error(f"An error occurred in the shop management application: {str(e)}")

if __name__ == "__main__":
    main()
