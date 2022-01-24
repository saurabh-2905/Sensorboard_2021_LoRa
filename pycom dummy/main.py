# 192.168.4.1
'''
pkt_format: |56 bytes msg(>12f4H)|4 bytes timestamp(>L)|4 bytes CRC(>L)|
'''
from network import LoRa
import socket, ustruct, network, machine, time, micropython

def crc32(crc, p, len):
  crc = 0xffffffff & ~crc
  for i in range(len):
    crc = crc ^ p[i]
    for j in range(8):
      crc = (crc >> 1) ^ (0xedb88320 & -(crc & 1))
  return 0xffffffff & ~crc


lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ, sf=7,
            preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON,
            tx_iq=False, rx_iq=False, public=True)


s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(True)

# Start of loop
_iteration_var = 0
while True:
    print(_iteration_var)
    _iteration_var += 1

    recv_msg = s.recv(64)
    if len(recv_msg) == 64:   #### to differentiate between heartbeat and msg
        if ustruct.unpack(">L", recv_msg[-4:])[0] != crc32(0, recv_msg[:-4], 60):
            print('Invalid CRC32')
        else:
            values = ustruct.unpack('>12f4H', recv_msg[:-8]) #### exclude timstamp and crc (8 bytes) to get msg
            timestamp = ustruct.unpack('>L', recv_msg[-8:-4]) ##### get timestamp
            print(values, timestamp)
            s.send(str(values[15])+','+str(timestamp[0]))
    else:
        print('Short message:', len(recv_msg))

    # except Exception as e:
    #     print('Reception Error:', e)