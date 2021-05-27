# Entered line after line into the REPL via serial connection
from network import LoRa

import socket
import ustruct

lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ, sf=7, preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON, tx_iq=False, rx_iq=False, public=True) # Tried here also public=False, rx_iq=True

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)
while True:
    

    msg = ustruct.unpack('iiiiiiiii',(s.recv(128))
    print(msg) 
    #print(s.recv(128).decode()) 
