from loguru import logger

class RGBLED:
    def __init__(self, config, board, rgbled_styles):
        self.label = config['label']
        self.id = config['id']
        self.board = board
        self.pins = config['connection']['pins']
        self.listen_to = config['preferences']['listen_to']
        self.rgbled_styles = rgbled_styles
        self.on_colors = self._get_color('on_colors', config['preferences'], 'RGBLED_on_color')
        self.off_colors = self._get_color('off_colors', config['preferences'], 'RGBLED_off_color')
        self.state = 'off'
        logger.debug(f"💡 RGB LED '{self.label}' initialized on board {self.board}, pins {self.pins}")

    def _get_color(self, color_key, preferences, style_key):
        device_color = preferences.get(color_key, {})
        if all(key in device_color for key in ['red', 'green', 'blue']):
            return [int(device_color['red'], 16), 
                    int(device_color['green'], 16), 
                    int(device_color['blue'], 16)]
        return self._get_color_from_style(style_key)

    def _get_color_from_style(self, color_key):
        style = self.rgbled_styles.get('RGBLED_button_styles', {}).get(color_key, {})
        return [style.get('red', 0xFFFF), style.get('green', 0xFFFF), style.get('blue', 0xFFFF)]

    def turn_on(self):
        self._set_color(self.on_colors)
        self.state = 'on'
        logger.debug(f"💡 RGB LED '{self.label}' turned on")

    def turn_off(self):
        self._set_color(self.off_colors)
        self.state = 'off'
        logger.debug(f"💡 RGB LED '{self.label}' turned off")

    def _set_color(self, colors):
        for i, pin in enumerate(self.pins):
            pwm_value = colors[i]  # No scaling needed, use the full 16-bit range
            self.board.set_pwm(pin, 0, pwm_value)

    def update(self, button_states):
        for button_id in self.listen_to:
            if button_states.get(button_id) == 'on':
                self.turn_on()
                return
        self.turn_off()

    def cleanup(self):
        self.turn_off()
        logger.debug(f"💡 RGB LED '{self.label}' cleaned up")

    def get_state(self):
        return self.state