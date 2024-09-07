import json
import os
from loguru import logger

class StyleManager:
    def __init__(self, styles_path=None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(self.base_dir, 'config')
        self.styles_path = styles_path or os.path.join(self.config_dir, 'styles.json')
        logger.debug(f"Using styles path: {self.styles_path}")
        self.styles = self.load_styles()

    def load_styles(self):
        if not os.path.exists(self.styles_path):
            logger.error(f"💢 Styles file not found: {self.styles_path}")
            return self.default_styles()

        try:
            with open(self.styles_path, 'r') as f:
                styles = json.load(f)
            return self.convert_hex_strings(styles)
        except json.JSONDecodeError as e:
            logger.error(f"💢 JSON decode error in styles file: {e}")
        except Exception as e:
            logger.error(f"💢 Failed to load styles: {e}")

        return self.default_styles()

    def convert_hex_strings(self, styles):
        for button_style in styles['RGBLED_button_styles'].values():
            for color in ['red', 'green', 'blue']:
                button_style[color] = int(button_style[color], 16)
        return styles

    def get_styles(self):
        return self.styles

    def default_styles(self):
        return {
            "RGBLED_button_styles": {
                "RGBLED_off_color": {
                    "name": "dark_blue",
                    "red": 0xFFFF,
                    "green": 0xFFFF,
                    "blue": 0xDFFF
                },
                "RGBLED_on_color": {
                    "name": "bright_purple",
                    "red": 0x0000,
                    "green": 0xFFFF,
                    "blue": 0x0000
                }
            }
        }
