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
PERCENTAGE_THRESHOLD = 1.2  # Threshold as a percentage of the mean off reading
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


# This version uses the average of the first readings and the min and max to calculate the stable min and maxs
# and then compares if they are outside of that.

# Function to read current value from ACS712 sensor
def read_current(channel):
    # Create an AnalogIn object for the specified channel
    try:
        reading = channel.voltage
        return reading
    except:
        print(f"Error reading channel {channel}")
        return None


# Gather initial "off" readings and calculate mean
def gather_off_readings(channel, num_samples=NUM_SAMPLES, samples_per_cycle=SAMPLES_PER_CYCLE):
    
    # Gather off readings
    off_readings = []
    sampled_cycles = []
    sampled_mins = []
    sampled_maxs = []

    for _ in range(num_samples):
        for _ in range(samples_per_cycle):
            reading = read_current(channel)
            if reading is not None:
                off_readings.append(reading)
        sampled_cycles.append(sum(off_readings) / len(off_readings))
        sampled_mins.append(min(off_readings))
        sampled_maxs.append(max(off_readings))
    absolute_min = min(sampled_mins)
    absolute_max = max(sampled_maxs)
    print(f"Sampled cycles averages: {sampled_cycles}")
    mean_sampled_cycles = statistics.mean(sampled_cycles)
    print(f"Mean of sampled cycles: {mean_sampled_cycles}. absolute_min: {absolute_min}, absolute_max: {absolute_max}")
    return mean_sampled_cycles, absolute_min, absolute_max


def caluculate_threshold(off_average, absolute_min, absolute_max, percentage_threshold=PERCENTAGE_THRESHOLD):
    min_threshold = absolute_min - ((off_average - absolute_min) * percentage_threshold)
    max_threshold = absolute_max + ((absolute_max - off_average) * percentage_threshold)
    print(f"Thresholds: {min_threshold}, {max_threshold}")
    return min_threshold, max_threshold

# Main function to monitor the appliance
def monitor_appliance(channel, min_threshold, max_threshold, sample_size=SAMPLES_PER_CYCLE):
    while True:
        current_readings = []
        for _ in range(sample_size):
            reading = read_current(channel)
            if reading is not None:
                current_readings.append(reading)  
            time.sleep(0.01)  # Adjust the delay as necessary
        
        if min(current_readings) < min_threshold or max(current_readings) > max_threshold:
            print(f"Appliance is ON {min(current_readings)} - max: {max(current_readings)}")
        else:
            print(f"Appliance is OFF {min(current_readings)} - max: {max(current_readings)}")

        
try:
    if __name__ == "__main__":
        print("Gathering off readings...")
        off_average, absolute_min, absolute_max = gather_off_readings(channel)
        min_threshold, max_threshold = caluculate_threshold(off_average, absolute_min, absolute_max)
        print("Monitoring appliance...")
        monitor_appliance(channel, min_threshold, max_threshold)

except KeyboardInterrupt:
    logger.info("Program interrupted by user")