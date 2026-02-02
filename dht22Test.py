import board
import adafruit_dht
import time

dht_device = adafruit_dht.DHT22(board.D6)# Replace D6 with your pin

while True:
    temperature = dht_device.temperature
    humidity = dht_device.humidity
    print(temperature, humidity)
    time.sleep(1)