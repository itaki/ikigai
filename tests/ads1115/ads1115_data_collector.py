import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import xlsxwriter
import datetime

ADDRESS = 0x4a
GAIN = 1  # Set gain to 1 for a full-scale voltage range of ±4.096V

# Initialize I2C bus and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=ADDRESS, gain=GAIN)  # Set the ADS1115 address to 0x4a with gain 1

# Initialize channels
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# Data collection for 1 minute
duration = 60  # seconds
start_time = time.time()
end_time = start_time + duration

# Prepare lists to store data
data_channel_0 = []
data_channel_1 = []
data_channel_2 = []
data_channel_3 = []

while time.time() < end_time:
    elapsed_time = time.time() - start_time
    print(f"\rElapsed Time: {elapsed_time:.2f} seconds", end="")

    # Read values from each channel and store in the corresponding list
    data_channel_0.append(chan0.voltage)
    data_channel_1.append(chan1.voltage)
    data_channel_2.append(chan2.voltage)
    data_channel_3.append(chan3.voltage)

    # Sleep for a short time to avoid flooding the data collection
    time.sleep(0.1)

# Prepare the timestamp for the file name
timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

# Convert the address to a hex string for the file name
address_str = f"0x{ADDRESS:02x}"

# Create the Excel file name
file_name = f"ads1115_{address_str}_{timestamp}.xlsx"

# Write data to an Excel file
workbook = xlsxwriter.Workbook(file_name)
worksheet = workbook.add_worksheet()

# Write headers
worksheet.write(0, 0, 'Channel 0 (V)')
worksheet.write(0, 1, 'Channel 1 (V)')
worksheet.write(0, 2, 'Channel 2 (V)')
worksheet.write(0, 3, 'Channel 3 (V)')

# Write data to the worksheet
for row in range(len(data_channel_0)):
    worksheet.write(row + 1, 0, data_channel_0[row])
    worksheet.write(row + 1, 1, data_channel_1[row])
    worksheet.write(row + 1, 2, data_channel_2[row])
    worksheet.write(row + 1, 3, data_channel_3[row])

# Close the workbook
workbook.close()

print(f"\nData collection complete. Data written to '{file_name}'")
