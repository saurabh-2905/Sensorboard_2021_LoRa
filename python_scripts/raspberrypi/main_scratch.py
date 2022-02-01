# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika Unnikrishnan, Saurabh Band
# date: 10.01.2022
# function: Implentation of a LoRa receiving LoPy, which after receiving checks
#           if any of the received data is not valid. If any data is not valid
#           it wont be send via MQTT, otherwise it will.
# -------------------------------------------------------------------------------
###testing git
from datetime import datetime

import paho.mqtt.client as mqtt

import loralib as lora
import threading
import time
import struct

def write_to_log(msg):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + get_date_and_time() + "\n")


def write_to_log_time(msg, timestamp):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + timestamp + "\n")


def get_date_and_time():
    """
    Return the current date and time as a string. Formatted like:
    "DAY.MONTH.YEAR -- HOUR:MINUTE:SECOND"
    """
    return datetime.now().strftime("%d.%m.%Y" + " -- " + "%H:%M:%S")


def lora_init():
    """
    Initialises the SX1276 with 868MHz and a SF of 7.
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


def connect_mqtt():
    """
    Connects RbPi to the MQTT Server with the specidfied IP-Address
    """
    try:
        CLIENT.connect(MQTT_SERVER)
    except Exception as em:
        write_to_log(str(em))


def cb():
    """
    Callbackfunction, that increments the counter for each board.
    If the value is at :param: MAX_COUNT, sends a value, that indicates
    that the board isn't working anymore.
    """
    global cb_timer_done
    cb_timer_done = True


def publish_failed_board(id_val):
    """
    Publsihed data, that indicates that the sensorboard is failed.
    """
    global k
    k = 0
    for j in range(length_failed_sensors):
        if k < 4:
            if k == 0:
                CLIENT.publish(topic=_TOPICS[k].format(id_val=id_val), payload="40002")
            elif k == 1:
                CLIENT.publish(topic=_TOPICS[k].format(id_val=id_val), payload="1002")
            elif k == 2:
                CLIENT.publish(topic=_TOPICS[k].format(id_val=id_val), payload="27")
            elif k == 3:
                CLIENT.publish(topic=_TOPICS[k].format(id_val=id_val), payload="1102")
            k += 1
        else:
            CLIENT.publish(topic=_TOPICS[k].format(id_val=id_val), payload="82")
            CLIENT.publish(topic=_TOPICS[k+1].format(id_val=id_val), payload="102")
            k += 2


def publish_failed_sensors(id_val_index):
    """
    Publishes all Sensorstatus' to the MQTT Server.
    """
    id_val = str(id_val_index)
    i = 0
    for j in range(length_failed_sensors):
        if i < 4:
            if sensor_connections[id_val_index-1][j]:
                if i == 0:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload="40002")
                elif i == 1:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload="1002")
                elif i == 2:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload="27")
                elif i == 3:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload="1102")
            i += 1
        else:
            if sensor_connections[id_val_index-1][j]:
                CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload="82")
                CLIENT.publish(topic=_TOPICS[i+1].format(id_val=id_val), payload="102")
            i += 2


def check_sensors(val, id_val):
    """
    Checks if any Sensors are sending invalid data, hence they are broken.
    """
    for i in range(length_failed_sensors):
        if val & comp_const:
            sensor_connections[id_val][i] = 1
            val = val >> comp_const
        else:
            sensor_connections[id_val][i] = 0
            val = val >> comp_const


def publish_limits_broken(id_val, limits_val):
    """
    Publishes if limits are broken for given board.
    """
    if limits_val:
        CLIENT.publish(topic=_Limits_broken.format(id_val=id_val), payload="1000")
    else:
        CLIENT.publish(topic=_Limits_broken.format(id_val=id_val), payload="10000")


def send_mqtt(values):
    """
    Sends given values to the MQTT Server. Also publishes information
    about working and not working sensors, given by :function: check_sensors.
    """
    connect_mqtt()
    id_val_index = values[15]
    id_val = str(id_val_index)
    publish_limits_broken(id_val_index, values[13])
    if not values[length_values]:
        for j in range(length_values):
            CLIENT.publish(topic=_TOPICS[j].format(id_val=id_val), payload=str(values[j]))
    else:
        check_sensors(values[length_values], id_val_index-1)
        i = 0
        for j in range(length_failed_sensors):
            if i < 4:
                if not sensor_connections[id_val_index-1][j]:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload=str(values[i]))
                i += 1
            else:
                if not sensor_connections[id_val_index-1][j]:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload=str(values[i]))
                    CLIENT.publish(topic=_TOPICS[i+1].format(id_val=id_val), payload=str(values[i+1]))
                i += 2
        publish_failed_sensors(id_val_index)


def crc32(crc, p, len):
    crc = 0xffffffff & ~crc
    for i in range(len):
        crc = crc ^ p[i]
        for j in range(8):
            crc = (crc >> 1) ^ (0xedb88320 & -(crc & 1))
    return 0xffffffff & ~crc


# Tuple with MQTT topics
_TOPICS = ("board{id_val}/co2_scd", "board{id_val}/co", "board{id_val}/o2", "board{id_val}/amb_press",
           "board{id_val}/temp1_am", "board{id_val}/humid1_am", "board{id_val}/temp2_am",
           "board{id_val}/humid2_am", "board{id_val}/temp3_am", "board{id_val}/humid3_am",
           "board{id_val}/temp4_am", "board{id_val}/humid4_am")

_Failed_times = "board{id_val}/active_status"  # Topic for the Sensorboardstatus
_Failed_sensor = "sensor{id_val}_stat_"  # Topic for the Sensorstatus
_Limits_broken = "board{id_val}/limits"
comp_const = 1
length_failed_sensors = 8
length_values = 12  # 12 sensor readings+sensor board number+limits broken+heartbeat+sensor id
cb_timer_done = False
sensorboard_list = dict()
board_ids = []

MAX_COUNT = 3  # Maximum of heartbeats that are allowed to be missed.

sensor_connections = [[0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0]]  # Holds all values for the working/not working sensors.

# Setting up MQTT
MQTT_SERVER = '192.168.30.17'
CLIENT = mqtt.Client()

# Connect WIFI and MQTT
MESSAGE_LENGTH = const(66)    ###### 58+4+4
_pkng_frmt = '>12f3HI'

lora_init()
connect_mqtt()
# timer_start()
print('Receiving Packets......')
# Start of loop
threading.Timer(90000, cb).start()
while True:
    recv_msg = receive()
    if len(recv_msg) == MESSAGE_LENGTH:   #### to differentiate between heartbeat and msg
        if struct.unpack(">L", recv_msg[-4:])[0] != crc32(0, recv_msg[:-4], 60):
            print('Invalid CRC32')
            write_to_log_time('Invalid CRC32', str(timestamp[0]))
        else:
            values = struct.unpack(_pkng_frmt, recv_msg[:-8]) #### exclude timstamp and crc (8 bytes) to get msg
            timestamp = list(struct.unpack('>L', recv_msg[-8:-4])) ##### get timestamp
            send(str(values[15])+','+str(timestamp[0]))
            write_to_log_time('Received', str(timestamp[0]))
            if values[15] not in board_ids:
                board_ids += [values[15]]
                sensorboard_list[values[15]] = 1
            else:
                sensorboard_list[values[15]] += 1
            l = list(values)
            print(l, timestamp)
            for i in range(len(l)):
                if i <= 3:
                    l[i] = round(l[i], 2)
                elif i <= 11:
                    l[i] = round(l[i], 1)

            if l[0] > 40000 or l[0] < 0 or l[1] > 1000 or l[1] < 0 or l[2] > 25 or l[2] < 0 or l[3] > 1100 or l[3] < 300 or l[4] > 80 or l[4] < -40 or l[5] > 100 or l[5] < 0 or l[6] > 80 or l[6] < -40 or l[7] > 100 or l[7] < 0 or l[8] > 80 or l[8] < -40 or l[9] > 100 or l[9] < 0 or l[10] > 80 or l[10] < -40 or l[11] > 100 or l[11] < 0 or l[12] > 255 or l[12] < 0 or l[13] < 0 or l[13] > 1 or l[15] > 4 or l[15] < 1:
                time.sleep(0.05)  # OPTIMIZE!
                # send(str(l[15]))
                print("Limit error for MQTT")
                write_to_log_time('Limit error for MQTT: {}'. format(l), str(timestamp[0]))

            else:
                send_mqtt(l)
                time.sleep(0.05)  # OPTIMIZE!
                # send(str(l[15]))
                print("Sent to MQTT")  # to be removed
    else:
        print('Short message:', len(recv_msg))
        write_to_log_time('Short message:{}'.format(len(recv_msg)), str(timestamp[0]))

    if cb_timer_done:
        for each_board in board_ids:
            signal_count = sensorboard_list[each_board]
            if signal_count < 2:
                print('Board {} not working'.format(each_board))
                CLIENT.publish(topic=_Failed_times.format(id_val=each_board), payload="10000")
                publish_failed_board("{}".format(each_board))
            else:
                print('signal_count:', signal_count)
            sensorboard_list[each_board] = 0
        # print('sensorboard_list:', sensorboard_list)
        cb_done = False









    # values = struct.unpack('>12f4I', recv_msg)
    # # Converting to list to obtain float subsitute
    # l = list(values)
    # print(l)
    # if not l[14]:
    #     for i in range(len(l)):
    #         if i <= 3:
    #             l[i] = round(l[i], 2)
    #         elif i <= 11:
    #             l[i] = round(l[i], 1)
    #     # prevent spikes. Values are specified by the datasheets.
    #     if l[0] > 40000 or l[0] < 0 or l[1] > 1000 or l[1] < 0 or l[2] > 25 or l[2] < 0 or l[3] > 1100 or l[3] < 300 or l[4] > 80 or l[4] < -40 or l[5] > 100 or l[5] < 0 or l[6] > 80 or l[6] < -40 or l[7] > 100 or l[7] < 0 or l[8] > 80 or l[8] < -40 or l[9] > 100 or l[9] < 0 or l[10] > 80 or l[10] < -40 or l[11] > 100 or l[11] < 0 or l[12] > 255 or l[12] < 0 or l[13] < 0 or l[13] > 1 or l[15] > 4 or l[15] < 1:
    #         time.sleep(0.05)  # OPTIMIZE!
    #         # send(str(l[15]))
    #         print("SEND")
    #     else:
    #         send_mqtt(l)
    #         time.sleep(0.05)  # OPTIMIZE!
    #         # send(str(l[15]))
    #         print("SEND")  # to be removed
    # else:
    #     val_hb = l[15]
    #     send(str(l[15]))
    #     if val_hb == 1:
    #         counter_board1 = 0
    #         CLIENT.publish(topic=_Failed_times.format(id_val=1), payload="1000")
    #     elif val_hb == 2:
    #         counter_board2 = 0
    #         CLIENT.publish(topic=_Failed_times.format(id_val=2), payload="1000")
    #     elif val_hb == 3:
    #         counter_board3 = 0
    #         CLIENT.publish(topic=_Failed_times.format(id_val=3), payload="1000")
    #     elif val_hb == 4:
    #         counter_board4 = 0
    #         CLIENT.publish(topic=_Failed_times.format(id_val=4), payload="1000")
