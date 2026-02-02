import time
import adafruit_sgp40
import board


i2c = board.I2C()  # uses board.SCL and board.SDA
sgp = adafruit_sgp40.SGP40(i2c)
x=0
while True:
    print("Measurement: ", sgp.raw)
    print("")
    print("Measurement index: ", sgp.measure_index(71, 51))
    time.sleep(1)
    x+=1