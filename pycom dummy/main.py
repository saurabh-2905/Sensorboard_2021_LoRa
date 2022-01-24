# 192.168.4.1

from network import LoRa
import socket, ustruct, ubinascii, network, machine, time, micropython


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

    try:
        recv_msg = s.recv(56)
        values = ustruct.unpack('>12f4H', recv_msg)
        print(values)
        s.send(str(values[15]))

    except Exception as e:
        print('Reception Error:', e)