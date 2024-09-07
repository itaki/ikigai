from adafruit_pca9685 import PCA9685 as Adafruit_PCA9685
from loguru import logger

class PCA9685:
    def __init__(self, i2c, config, app_config):
        self.i2c_address = int(config['i2c_address'], 16)
        self.mode = config.get('purpose', 'LED Control')  # Default to LED Control if not specified

        try:
            # Initialize the Adafruit PCA9685 object
            self.pca = Adafruit_PCA9685(i2c, address=self.i2c_address)
            if self.mode == 'Servo Control':
                frequency = config.get('frequency', 50)  # Default to 50Hz for servos
                self.set_frequency(frequency)
                logger.info(f"🔮 Initialized PCA9685 at address {hex(self.i2c_address)} in Servo Control mode with frequency {frequency}Hz as board ID {config['id']}")
            else:
                frequency = config.get('frequency', 1000)  # Default to 1000Hz for LEDs
                self.set_frequency(frequency)
                logger.info(f"🔮 Initialized PCA9685 at address {hex(self.i2c_address)} in LED Control mode with frequency {frequency}Hz as board ID {config['id']}")
        except Exception as e:
            logger.error(f"💢 Failed to initialize PCA9685 at address {hex(self.i2c_address)}: {str(e)}")
            raise e

    @property
    def channels(self):
        """Expose channels from the underlying Adafruit_PCA9685 instance."""
        return self.pca.channels

    def set_frequency(self, frequency):
        """Set the PWM frequency in Hz."""
        self.pca.frequency = frequency

    def set_pwm(self, channel, on, off):
        """Set the PWM on/off values for a specific channel."""
        self.pca.channels[channel].duty_cycle = off

    def set_pwm_value(self, channel, value):
        """Set the PWM duty cycle as a 16-bit value (0-65535)."""
        self.pca.channels[channel].duty_cycle = value

    def set_servo_angle(self, channel, angle):
        """Set the servo angle for a specific channel."""
        min_pulse = 1000  # Minimum pulse width (in microseconds)
        max_pulse = 2000  # Maximum pulse width (in microseconds)
        pulse_range = max_pulse - min_pulse
        angle_range = 180  # Full range of servo angles (typically 0-180 degrees)

        # Calculate duty cycle value for the given angle
        pulse_width = min_pulse + (pulse_range * angle / angle_range)
        duty_cycle_value = int((pulse_width * 65535) / (1000000 / self.pca.frequency))

        # Set the duty cycle for the specified channel
        self.set_pwm_value(channel, duty_cycle_value)
