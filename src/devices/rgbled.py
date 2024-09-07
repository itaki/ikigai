from loguru import logger

class RGBLED:
    def __init__(self, config, board, rgbled_styles):
        self.label = config['label']
        self.id = config['id']
        self.board = board
        self.pins = config['connection']['pins']
        self.listen_to = config['preferences']['listen_to']
        self.rgbled_styles = rgbled_styles
        self.on_colors = self._get_color_from_style('RGBLED_on_color')
        self.off_colors = self._get_color_from_style('RGBLED_off_color')
        self.state = 'off'
        logger.debug(f"💡 RGB LED '{self.label}' initialized on board {self.board}, pins {self.pins}")

    def _get_color_from_style(self, color_key):
        style = self.rgbled_styles.get('RGBLED_button_styles', {}).get(color_key, {})
        return [style.get('red', 0xFFFF), style.get('green', 0xFFFF), style.get('blue', 0xFFFF)]

    def turn_on(self):
        self._set_color(self.on_colors)
        self.state = 'on'
        logger.debug(f"💡 RGB LED '{self.label}' turned on with color {self.rgbled_styles['RGBLED_button_styles']['RGBLED_on_color']['name']}")

    def turn_off(self):
        self._set_color(self.off_colors)
        self.state = 'off'
        logger.debug(f"💡 RGB LED '{self.label}' turned off with color {self.rgbled_styles['RGBLED_button_styles']['RGBLED_off_color']['name']}")

    def _set_color(self, colors):
        for i, pin in enumerate(self.pins):
            # MCP23017 expects values from 0 to 4095, but our colors are in 16-bit range (0-65535)
            pwm_value = colors[i]  # No need to invert as we're using common anode LEDs
            scaled_value = pwm_value // 16  # Scale 0-65535 to 0-4095
            self.board.set_pwm(pin, 0, scaled_value)

    def update(self, button_states):
        for button_id in self.listen_to:
            if button_states.get(button_id) == 'on':
                self.turn_on()
                return
        self.turn_off()

    def cleanup(self):
        self.turn_off()
        logger.debug(f"💡 RGB LED '{self.label}' cleaned up")
