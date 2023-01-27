# 192.168.4.1
'''
pkt_format: |56 bytes msg(>12f4H)|4 bytes timestamp(>L)|4 bytes CRC(>L)|
'''
# from collections import defaultdict
from network import LoRa
import socket, ustruct, network, machine, time, micropython
from machine import Timer

def crc32(crc, p, len):
    crc = 0xffffffff & ~crc
    for i in range(len):
        crc = crc ^ p[i]
        for j in range(8):
            crc = (crc >> 1) ^ (0xedb88320 & -(crc & 1))
    return 0xffffffff & ~crc


def write_to_log(msg, timestamp):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + timestamp + "\n")


def cb(t):
    global cb_done
    cb_done = True

sensorboard_list = dict()
board_ids = []

MESSAGE_LENGTH = const(66)
_pkng_frmt = '>12f3HI'

cb_done = False

lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ, sf=7,
            preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON,
            tx_iq=False, rx_iq=False, public=True)


s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(True)

# Create Timers
timer0 = Timer.Chrono()

# Start of loop
_iteration_var = 0
print('Receiving Packets......')
timer0.start()
while True:
    print(_iteration_var)
    _iteration_var += 1

    recv_msg = s.recv(MESSAGE_LENGTH)
    if len(recv_msg) == MESSAGE_LENGTH:   #### to differentiate between heartbeat and msg
        if ustruct.unpack(">L", recv_msg[-4:])[0] != crc32(0, recv_msg[:-4], 60):
            print('Invalid CRC32')
            write_to_log('Invalid CRC32', str(timestamp[0]))
        else:
            values = ustruct.unpack(_pkng_frmt, recv_msg[:-8]) #### exclude timstamp and crc (8 bytes) to get msg
            timestamp = ustruct.unpack('>L', recv_msg[-8:-4]) ##### get timestamp
            print(values, timestamp)
            s.send(str(values[15])+','+str(timestamp[0]))
            if values[15] not in board_ids:
                board_ids += [values[15]]
                sensorboard_list[values[15]] = 1
            else:
                sensorboard_list[values[15]] += 1

            write_to_log('Received', str(timestamp[0]))
    else:
        print('Short message:', len(recv_msg))
        write_to_log('Short message:{}'.format(len(recv_msg)), str(timestamp[0]))

    if timer0.read() >= 90:
        # timer0.stop()
        for each_board in board_ids:
            signal_count = sensorboard_list[each_board]
            if signal_count < 2:
                print('Board {} not working'.format(each_board))
            else:
                print('signal_count:', signal_count)
            sensorboard_list[each_board] = 0
        print('sensorboard_list:', sensorboard_list)
        cb_done = False
        timer0.reset()
        # timer0.start()


    # except Exception as e:
    #     print('Reception Error:', e)