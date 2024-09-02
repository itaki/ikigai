import json
import os
import logging

logger = logging.getLogger("shop_logger")

class ConfigLoader:
    def __init__(self, config_path='config/config.json', gates_config_path='config/gates.json'):
        self.config_path = config_path
        self.gates_config_path = gates_config_path
        self.config = {}
        self.gates_config = {}

    def load_config(self):
        """Load the main configuration file."""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)
            logger.debug(f"Main configuration loaded from {self.config_path}")
            self.validate_config(self.config)

    def load_gates_config(self):
        """Load the gates configuration file."""
        if not os.path.exists(self.gates_config_path):
            logger.error(f"Gates config file not found: {self.gates_config_path}")
            raise FileNotFoundError(f"Gates config file not found: {self.gates_config_path}")
        
        with open(self.gates_config_path, 'r') as file:
            self.gates_config = json.load(file)
            logger.debug(f"Gates configuration loaded from {self.gates_config_path}")
            self.validate_gates_config(self.gates_config)

    def validate_config(self, config):
        """Validate the main configuration."""
        required_keys = ['boards', 'tools']
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required key in config: {key}")
                raise ValueError(f"Missing required key in config: {key}")
        logger.debug("Main configuration validation passed.")

    def validate_gates_config(self, gates_config):
        """Validate the gates configuration."""
        required_keys = ['gates']
        for key in required_keys:
            if key not in gates_config:
                logger.error(f"Missing required key in gates config: {key}")
                raise ValueError(f"Missing required key in gates config: {key}")
        logger.debug("Gates configuration validation passed.")

    def get_boards(self):
        """Return the boards configuration."""
        return self.config.get('boards', [])

    def get_tools(self):
        """Return the tools configuration."""
        return self.config.get('tools', [])

    def get_gates(self):
        """Return the gates configuration."""
        return self.gates_config.get('gates', [])

    def reload_configs(self):
        """Reload both the main and gates configurations."""
        self.load_config()
        self.load_gates_config()
        logger.debug("Both main and gates configurations reloaded.")

# Example usage:
if __name__ == "__main__":
    config_loader = ConfigLoader()
    try:
        config_loader.reload_configs()
        boards = config_loader.get_boards()
        tools = config_loader.get_tools()
        gates = config_loader.get_gates()

        logger.debug(f"Boards: {boards}")
        logger.debug(f"Tools: {tools}")
        logger.debug(f"Gates: {gates}")
    except Exception as e:
        logger.error(f"Failed to load configurations: {str(e)}")
