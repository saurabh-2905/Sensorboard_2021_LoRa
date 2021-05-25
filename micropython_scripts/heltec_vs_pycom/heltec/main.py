"""
https://github.com/lemariva/uPyLoRaWAN
"""

from machine import Pin, SPI
import utime as time
from config import *

from sx127x import SX127x

device_spi = SPI(baudrate = 10000000, 
        polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
        sck = Pin(device_config['sck'], Pin.OUT, Pin.PULL_DOWN),
        mosi = Pin(device_config['mosi'], Pin.OUT, Pin.PULL_UP),
        miso = Pin(device_config['miso'], Pin.IN, Pin.PULL_UP))

lora = SX127x(device_spi, pins=device_config, parameters=lora_parameters)


nextTx = time.time() + 5

counter = 0

while True:
    if lora.received_packet():
        payload = lora.read_payload()
        print("Received:", payload.decode())

    if time.time() > nextTx:
        print("Sending counter", counter)
        lora.println(str(counter))
        counter += 1
        nextTx = time.time() + 5
