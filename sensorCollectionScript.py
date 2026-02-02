import board
import adafruit_dht
import time
import sys
import os
import adafruit_sgp40
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from DFRobot_MultiGasSensor import *



dht22Sensor = adafruit_dht.DHT22(board.D6)# Replace D6 with your pin
#Sets NH3 Sensor reading type to UART which is how it is wired
gas = DFRobot_MultiGasSensor_UART(9600)

def setup():
  #Mode of obtaining data: the main controller needs to request the sensor for data
    while (False == gas.change_acquire_mode(gas.NH3)):
        print("wait acquire mode change!")
        time.sleep(1)
    print("change acquire mode success!")
    gas.set_temp_compensation(gas.ON)
    time.sleep(1)
    
def loop():
  # Gastype is set while reading the gas level. Must first perform a read before
  # attempting to use it.
    con = gas.read_gas_concentration()
    print ("Ambient "+ gas.gastype + " concentration: %.2f " % con + gas.gasunits + " temp: %.1fC" % gas.temp)
    time.sleep(1) 

setup()
while True:
    temperature = dht22Sensor.temperature
    humidity = dht22Sensor.humidity
    print(temperature, humidity)
    sgp40AdjustedMeasurement = sgp.measure_index(temperature, humidity)
    try:
        loop()
    except Exception as e:
        print("there is error",e) 
    time.sleep(1)