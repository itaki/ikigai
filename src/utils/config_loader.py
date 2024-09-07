import json
import os
from loguru import logger

class ConfigLoader:
    def __init__(self):
        self.app_config = None
        self.boards = None
        self.devices = None
        self.gates = None

    def reload_configs(self):
        try:
            with open('src/config/app_config.json', 'r') as f:
                self.app_config = json.load(f)
            with open('src/config/boards.json', 'r') as f:
                self.boards = json.load(f)
            with open('src/config/devices.json', 'r') as f:
                self.devices = json.load(f)
            with open('src/config/gates.json', 'r') as f:
                self.gates = json.load(f)
            logger.info("✅ All configurations loaded successfully")
        except Exception as e:
            logger.error(f"💢 Error loading configurations: {str(e)}")
            raise

    def get_app_config(self):
        return self.app_config

    def load_config(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"💢 Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"💢 JSON decode error in configuration file {file_path}: {e}")
        except Exception as e:
            logger.error(f"💢 Failed to load configuration file {file_path}: {e}")
        return {}

    def get_boards(self):
        return self.boards

    def get_devices(self):
        return self.devices

    def get_gates(self):
        return self.gates

# Example usage:
if __name__ == "__main__":
    config_loader = ConfigLoader()
    try:
        config_loader.reload_configs()
        boards = config_loader.get_boards()
        tools = config_loader.get_devices()
        gates = config_loader.get_gates()

        logger.debug(f"Boards: {boards}")
        logger.debug(f"Tools: {tools}")
        logger.debug(f"Gates: {gates}")
    except Exception as e:
        logger.error(f"Failed to load configurations: {str(e)}")
