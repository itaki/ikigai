import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import numpy as np

# Constants
ADDRESS = 0x48                # ADS1115 address
SAMPLES_PER_CYCLE = 100       # Number of samples per AC cycle (60Hz)
AC_CYCLE_FREQUENCY = 60       # AC frequency in Hz (60Hz in the US, 50Hz in some regions)
SAMPLE_DURATION = 1 / (AC_CYCLE_FREQUENCY * SAMPLES_PER_CYCLE)
THRESHOLD_ON = 0.5            # Threshold voltage to consider the device "on" (adjust as needed)
THRESHOLD_OFF = 0.1           # Threshold voltage to consider the device "off" (adjust as needed)
NUM_CYCLES_TO_SAMPLE = 5      # Number of AC cycles to sample
RMS_THRESHOLD = 0.3           # RMS voltage threshold to consider the device "on" (adjust as needed)

# Initialize I2C bus and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=ADDRESS)  # Set the ADS1115 address to 0x4a

# Initialize channel (Assuming channel 0 is connected to ACS712)
chan = AnalogIn(ads, ADS.P0)

def calculate_rms(values):
    """Calculate the RMS value from a list of voltage readings."""
    return np.sqrt(np.mean(np.square(values)))

def collect_samples(num_samples, sample_duration):
    """Collects voltage samples over a specified number of samples and duration."""
    samples = []
    for _ in range(num_samples):
        samples.append(chan.voltage)
        time.sleep(sample_duration)
    return samples

def is_device_on(rms_value, threshold):
    """Determines if the device is on based on the RMS value."""
    return rms_value > threshold

def main():
    print("Starting ACS712 device status detection...")

    while True:
        try:
            # Collect samples for a given number of AC cycles
            num_samples = SAMPLES_PER_CYCLE * NUM_CYCLES_TO_SAMPLE
            samples = collect_samples(num_samples, SAMPLE_DURATION)

            # Calculate RMS value
            rms_value = calculate_rms(samples)
            print(f"RMS Voltage: {rms_value:.3f} V")

            # Determine if the device is on or off
            if is_device_on(rms_value, RMS_THRESHOLD):
                print("Device is ON")
            else:
                print("Device is OFF")

            time.sleep(1)  # Delay before the next check (adjust as needed)

        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
