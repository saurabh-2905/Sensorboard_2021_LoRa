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
import numpy as np
import pickle

def write_to_log(msg):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + get_date_and_time() + "\n")


def write_to_log_time(msg, timestamp, rx_timestamp):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + timestamp + "\t" + rx_timestamp + "\n")


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
            sensor_connections[id_val][i] = 1   ### sensor faulty
            val = val >> comp_const
        else:
            sensor_connections[id_val][i] = 0   ### sensor normal
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
    id_val_index = map_board_ids(values[15])   ### get the integer board id from the hardware board id
#     print(id_val_index)
    id_val = str(id_val_index)
    publish_limits_broken(id_val_index, values[13])
    if not values[length_values]:   ### check the sensor status bit
        for j in range(length_values):
            CLIENT.publish(topic=_TOPICS[j].format(id_val=id_val), payload=str(values[j]))
    else:
        check_sensors(values[length_values], id_val_index-1)  ### subtract 1 from id_val since board number start from 1 but indexing start from 0
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


def map_board_ids(hardware_id):
    '''
    map the new hardware ids to the old integer id for compatibility with code
    '''
    global board_ids
    mapped_id = np.where(np.array(board_ids) == hardware_id)[0][0]
    return mapped_id + 1
    

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
length_values = 12  # 12 sensor readings+sensor board status+limits broken+heartbeat+sensor id
cb_timer_done = False
sensorboard_list = dict()
board_ids = [3982231425, 94420780, 301920073]   ### based on the manuall numbering of the boards (to map to old ids)

MAX_COUNT = 3  # Maximum of heartbeats that are allowed to be missed.

sensor_connections = [[0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0]]  # Holds all values for the working/not working sensors.

# Setting up MQTT
MQTT_SERVER = '192.168.30.17'
CLIENT = mqtt.Client()

# Connect WIFI and MQTT
MESSAGE_LENGTH = 66    ###### 58+4+4
_pkng_frmt = '>12f3HI'

lora_init()
connect_mqtt()
# timer_start()
print('Receiving Packets......')
# Start of loop
threading.Timer(90, cb).start()
all_values = []
while True:
    recv_msg = receive()
    if len(recv_msg) == MESSAGE_LENGTH:   #### to differentiate between heartbeat and msg
        if struct.unpack(">L", recv_msg[-4:])[0] != crc32(0, recv_msg[:-4], 60):
            print('Invalid CRC32')
            receiver_timestamp = time.localtime()
            rx_datetime = [receiver_timestamp.tm_year, receiver_timestamp.tm_mon, receiver_timestamp.tm_mday, receiver_timestamp.tm_hour, receiver_timestamp.tm_min, receiver_timestamp.tm_sec]
            write_to_log_time('Invalid CRC32', str(timestamp[0]), str(rx_datetime))
        else:
            values = struct.unpack(_pkng_frmt, recv_msg[:-8]) #### exclude timstamp and crc (8 bytes) to get msg
            timestamp = list(struct.unpack('>L', recv_msg[-8:-4])) ##### get timestamp
            receiver_timestamp = time.localtime()
            rx_datetime = [receiver_timestamp.tm_year, receiver_timestamp.tm_mon, receiver_timestamp.tm_mday, receiver_timestamp.tm_hour, receiver_timestamp.tm_min, receiver_timestamp.tm_sec]
            send(str(values[15])+','+str(timestamp[0]))
#            print(values + tuple(timestamp) + tuple([receiver_timestamp.tm_year, receiver_timestamp.tm_mon, receiver_timestamp.tm_mday, receiver_timestamp.tm_hour, receiver_timestamp.tm_min, receiver_timestamp.tm_sec]))
            all_values += [values + tuple(timestamp) + tuple(rx_datetime)]
            write_to_log_time( 'Received', str(timestamp[0]), str(rx_datetime) )
            if values[15] not in list(sensorboard_list.keys()):
#                 board_ids += [values[15]]
                sensorboard_list[values[15]] = 1
            else:
                sensorboard_list[values[15]] += 1
            l = list(values)
            print(l, timestamp, [receiver_timestamp.tm_year, receiver_timestamp.tm_mon, receiver_timestamp.tm_mday, receiver_timestamp.tm_hour, receiver_timestamp.tm_min, receiver_timestamp.tm_sec])
            for i in range(len(l)):
                if i <= 3:
                    l[i] = round(l[i], 2)
                elif i <= 11:
                    l[i] = round(l[i], 1)

            send_mqtt(l)
            print("Sent to MQTT")
    else:
        print('Short message:', len(recv_msg))
        write_to_log_time('Short message:{}'.format(len(recv_msg)), str(timestamp[0]), str(rx_datetime))

    if cb_timer_done:
        for each_board in list(sensorboard_list.keys()):
            print(each_board)
            old_board_id = map_board_ids(each_board)
            signal_count = sensorboard_list[each_board]
            if signal_count < 2:
                print('Board {} not working'.format(old_board_id))
                CLIENT.publish(topic=_Failed_times.format(id_val=old_board_id), payload="10000")
                publish_failed_board("{}".format(old_board_id))
            else:
                print('signal_count:', signal_count)
                CLIENT.publish(topic=_Failed_times.format(id_val=old_board_id), payload="1000")
            sensorboard_list[each_board] = 0

        with open('sensor_values_raspbery.pkl', 'wb') as f:   ### store the values for visualization
            pickle.dump(all_values, f)
        # print('sensorboard_list:', sensorboard_list)
        cb_timer_done = False
        threading.Timer(90, cb).start()


