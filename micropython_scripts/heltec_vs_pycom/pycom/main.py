
from network import LoRa
import socket
import machine
import time

# initialise LoRa in LORA mode
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
# more params can also be given, like frequency, tx power and spreading factor
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)

# create a raw LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

time.sleep(2)

counter = 0

nextTx = time.time() + 5 # send in 5 secs

print("Starting loop")

while True:
    if time.time() > nextTx:
        print("Sending packet", counter)
        # send some data
        s.setblocking(True)
        s.send(str(counter))
        s.setblocking(False)
        counter += 1
        nextTx = time.time() + 5
        
    
    data = s.recv(64)
    if len(data) > 0:
        print("Received", data.decode())