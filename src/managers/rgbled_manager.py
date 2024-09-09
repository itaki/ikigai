from loguru import logger
from devices.rgbled import RGBLED

class RGBLEDManager:
    def __init__(self, device_config, boards, rgbled_styles):
        self.boards = boards
        self.rgb_leds = {}
        self.rgbled_styles = rgbled_styles
        self.initialize_rgbleds(device_config)

    def initialize_rgbleds(self, device_config):
        for device in device_config:
            if device['type'] == 'RGBLED':
                board = self.boards.get(device['connection']['board'])
                if board:
                    rgbled = RGBLED(device, board, self.rgbled_styles)
                    self.rgb_leds[device['id']] = rgbled
                    logger.info(f"✅ RGB LED {rgbled.label} initialized on board {device['connection']['board']}")
                else:
                    logger.error(f"❌ Board {device['connection']['board']} not found for RGB LED {device['label']}")

    def set_led_state(self, led_id, state):
        led = self.rgb_leds.get(led_id)
        if led:
            if state == 'on':
                led.turn_on()
            elif state == 'off':
                led.turn_off()
            else:
                logger.error(f"Invalid state '{state}' for LED {led_id}")
        else:
            logger.error(f"LED {led_id} not found")

    def cleanup(self):
        logger.info("🧹 Cleaning up RGBLEDManager")
        for led in self.rgb_leds.values():
            led.cleanup()
        logger.info("✅ RGBLEDManager cleanup completed")