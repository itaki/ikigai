import board
import busio
import adafruit_pca9685
import time
from adafruit_servokit import ServoKit
kit = ServoKit(channels=16, address=0x72)
# i2c = busio.I2C(board.SCL, board.SDA)
# hat = adafruit_pca9685.PCA9685(i2c)
min = 70
max = 110

while True:
    for gate in range(0, 3):
        kit.servo[gate].angle = min 
        time.sleep(.5)
        kit.servo[gate].angle = max
