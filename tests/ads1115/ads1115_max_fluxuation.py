import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import statistics
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
NUM_SAMPLES = 10
SAMPLES_PER_CYCLE = 50
PERCENTAGE_THRESHOLD = 1.5  # Threshold as a percentage of the mean off reading
ADDRESS = 0x48
GAIN = 1

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the ADS1115 ADC (address 0x49)
ads = ADS.ADS1115(i2c, address=ADDRESS, gain=GAIN)
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

channel = chan3
# Function to read current value from ACS712 sensor
def read_current(channel):
    # Create an AnalogIn object for the specified channel
    reading = channel.voltage
    return reading


# Gather initial "off" readings and calculate mean
def gather_off_readings(channel, num_samples=NUM_SAMPLES, samples_per_cycle=SAMPLES_PER_CYCLE):
    
    # Gather off readings
    off_readings = []
    sampled_cycles = []
    max_fluctuation = 0
    for _ in range(num_samples):
        for _ in range(samples_per_cycle):
            off_readings.append(read_current(channel))
        sampled_cycles.append(max(off_readings) - min(off_readings))
    print(f"Sampled cycles: {sampled_cycles}")
    mean_sampled_cycles = statistics.mean(sampled_cycles)
    return mean_sampled_cycles


def caluculate_threshold(off_std, percentage_threshold=PERCENTAGE_THRESHOLD):
    threshold = off_std * percentage_threshold
    return threshold 

# Main function to monitor the appliance
def monitor_appliance(channel, threshold,sample_size=SAMPLES_PER_CYCLE):
    while True:
        current_readings = [read_current(channel) for _ in range(sample_size)]
        flux = max(current_readings) - min(current_readings)
        
        
        if flux > threshold:
            print(f"Appliance is ON (Max Current: {flux} A, Threshold: {threshold} A)")
        else:
            print(f"Appliance is OFF (Max Current: {flux} A, Threshold: {threshold} A)")

        time.sleep(0.1)  # Adjust the delay as necessary
try:
    if __name__ == "__main__":
        print("Gathering off readings...")
        off_std = gather_off_readings(channel)
        print(f"Off max fluxuation: {off_std} A")
        threshold = caluculate_threshold(off_std)
        print(f"Threshold: {threshold} A")
        print("Monitoring appliance...")
        monitor_appliance(channel, threshold=threshold)
except KeyboardInterrupt:
    logger.info("Program interrupted by user")