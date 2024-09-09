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
            self.app_config = self.load_config('src/config/app_config.json')
            self.boards = self.load_config('src/config/boards.json')
            self.devices = self.load_config('src/config/devices.json')
            self.gates = self.load_config('src/config/gates.json')
        except Exception as e:
            logger.error(f"💥 Error loading configurations: {str(e)}")
            raise

    def get_app_config(self):
        return self.app_config

    def load_config(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"📁 Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"🔧 JSON decode error in configuration file {file_path}: {e}")
        except Exception as e:
            logger.error(f"💥 Failed to load configuration file {file_path}: {e}")
        return {}

    def get_boards(self):
        return self.boards

    def get_devices(self):
        return self.devices

    def get_gates(self):
        return self.gates
