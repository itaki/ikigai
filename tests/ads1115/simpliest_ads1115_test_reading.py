import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time

ADDRESS = 0x4a # 4a for island, 48 for main
GAIN = 1
DATA_RATE = 128 # Set the desired data rate in samples per second (SPS)
NUMBER_OF_READINGS = 100  
BREATH_BETWEEN_READINGS = 1.0 / DATA_RATE  # Calculate the sleep time between readings based on the data rate

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize ADS1115 at address 0x49
ads = ADS.ADS1115(i2c, address=ADDRESS, gain=GAIN)
ads.data_rate = DATA_RATE

# Create a single-ended input on channel 0 (P0)
chan = AnalogIn(ads, ADS.P0)

# Continuously read the voltage
try:
    start_time = time.time()
    for i in range(NUMBER_OF_READINGS):
        reading = chan.voltage
        print(f"Voltage: {reading} V")
        #time.sleep(BREATH_BETWEEN_READINGS)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} s")
except KeyboardInterrupt:
    print("Script interrupted by user.")
