# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika Unnikrishnan, Saurabh Band
# date: 04.04.2022
# function: Implentation of a LoRa receiving LoPy, which after receiving checks
#           if any of the received data is not valid. If any data is not valid
#           it wont be send via MQTT, otherwise it will.
# -------------------------------------------------------------------------------

from datetime import datetime

import paho.mqtt.client as mqtt

import loralib as lora
import threading
import time
import struct
import numpy as np
import pickle


def write_to_log(msg):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + ";" + get_date_and_time() + "\n")


def get_date_and_time():
    """
    Return the current date and time as a string. Formatted like:
    "DAY.MONTH.YEAR -- HOUR:MINUTE:SECOND"
    """
    return datetime.now().strftime("%d.%m.%Y" + " -- " + "%H:%M:%S")


def lora_init():
    """
    Initialises the SX1276 with 868MHz and a SF of 7.
    Default BW: .
    Default CR: .
    """
    lora.init(868000000, 7)


def receive():
    """
    Waits for a message and returns it.
    """
    lora.changemode(1)
    while True:
        msg = lora.recv()[0]
        if msg:
            return msg


def send(msg):
    """
    Sends a given bytestring, or formats a string and then sends it.
    """
    lora.changemode(0)
    if isinstance(msg, str):
        msg = msg.encode()
    lora.send(msg)


def cb():
    """
    Callback setting a boolean indicating that the timer is/was done.
    """
    global cb_timer_done
    cb_timer_done = True


def crc32(crc, p, len):
    """
    Returns crc32 for a given length.
    """
    crc = 0xffffffff & ~crc
    for i in range(len):
        crc = crc ^ p[i]
        for j in range(8):
            crc = (crc >> 1) ^ (0xedb88320 & -(crc & 1))
    return 0xffffffff & ~crc

cb_timer_done = False

# Maximum of heartbeats that are allowed to be missed.
MAX_COUNT = 3

# Holds all values for the working/not working sensors.
sensor_connections = [[0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0]]

# Connect WIFI and MQTT
MESSAGE_LENGTH = 66  # 58+4+4
_pkng_frmt = '>12f3HI'

lora_init()
print("Receiving Packets......")
write_to_log("Receiving Packtes")
# Start of loop
threading.Timer(90, cb).start()
all_values = []
while True:
    recv_msg = receive()
    if len(recv_msg) == MESSAGE_LENGTH:  # to differentiate between heartbeat and msg
        if struct.unpack(">L", recv_msg[-4:])[0] != crc32(0, recv_msg[:-4], 62):
            print("Invalid CRC32 in msg")
            write_to_log("Invalid CRC32 in msg")
        else:
            # exclude timstamp and crc (8 bytes) to get msg
            values = struct.unpack(_pkng_frmt, recv_msg[:-8])
            timestamp = list(struct.unpack(">L", recv_msg[-8:-4]))

            # send ACK
            send(str(values[15]) + ',' + str(timestamp[0]))

            value_list = list(values)
            write_to_log(str(value_list[4:12]))
            print("Message received: ")
            print(value_list)
            for i in range(len(value_list)):
                if i <= 3:
                    value_list[i] = round(value_list[i], 2)
                elif i <= 11:
                    value_list[i] = round(value_list[i], 1)
    else:
        write_to_log("Error in msg")

    # checks if any boards are not working
    if cb_timer_done:
        cb_timer_done = False
        threading.Timer(90, cb).start()
