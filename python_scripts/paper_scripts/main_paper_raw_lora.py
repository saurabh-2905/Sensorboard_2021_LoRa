# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika Unnikrishnan, Saurabh Band
# date: 24.06.2022
# function: Central LoRa receiver. Pushes data via MQTT to the Backend.
# -------------------------------------------------------------------------------

from datetime import datetime

import paho.mqtt.client as mqtt

import loralib as lora
import threading
import time
import struct
import numpy as np
import pickle

# ------------------------ function declaration -------------------------------


def log_data(msg):
    """
    logs data for later visualization
    """
    with open("data_log", "a") as f:
        f.write(msg)


def read_config(path="config"):
    """
    Reads the config file, to get the relevant board ids.
    """
    with open("config", "r") as f:
        config = f.read()
    config = config.split("\n")[0].split(",")
    for i in range(len(config)):
        config[i] = int(config[i])
    return config


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
        try:
            msg, prssi = lora.recv()[0:4:3]
            if msg:
                return (msg, prssi)
        except Exception:
            pass


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
    Callback setting a boolean indicating that the timer is/was done.
    """
    global cb_timer_done
    cb_timer_done = True


def publish_failed_sensors(id_val_index):
    """
    Publishes all Sensorstatus' to the MQTT Server.
    The published value is the highest value the corresponding
    sensor is able to return plus two.
    """
    id_val = str(id_val_index)
    i = 0
    for j in range(number_of_sensors):
        if i < 4:
            if sensor_connections[id_val_index-1][j]:
                if i == 0:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload="40002")
                elif i == 1:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload="1002")
                elif i == 2:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload="27")
                elif i == 3:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload="1102")
            i += 1
        else:
            if sensor_connections[id_val_index-1][j]:
                CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                               payload="82")
                CLIENT.publish(topic=_TOPICS[i+1].format(id_val=id_val),
                               payload="102")
            i += 2


def check_sensors(val, id_val):
    """
    Checks if any Sensors are sending invalid data, hence they are broken.
    """
    for i in range(number_of_sensors):
        if val & 1:
            sensor_connections[id_val][i] = 1  # sensor faulty
            val = val >> 1
        else:
            sensor_connections[id_val][i] = 0  # sensor normal
            val = val >> 1


def publish_limits_broken(id_val, limits_val):
    """
    Publishes if limits are broken for given board.
    """
    if limits_val:
        CLIENT.publish(topic=_Limits_broken.format(id_val=id_val),
                       payload="1000")
    else:
        CLIENT.publish(topic=_Limits_broken.format(id_val=id_val),
                       payload="10000")


def send_mqtt(values):
    """
    Sends given values to the MQTT Server. Also publishes information
    about working and not working sensors, given by :function: check_sensors.
    """
    connect_mqtt()
    # get the integer board id from the hardware board id
    id_val_index = map_board_ids(values[16])
    id_val = str(id_val_index)
    publish_limits_broken(id_val_index, values[14])
    if not values[length_values]:   # check the sensor status bit
        for j in range(length_values):
            CLIENT.publish(topic=_TOPICS[j].format(id_val=id_val),
                           payload=str(values[j]))
    else:
        # subtract 1 from id_val_index since board number start
        # from 1, but indexing starts from 0
        check_sensors(values[length_values], id_val_index-1)
        i = 0
        for j in range(number_of_sensors):
            if i < 4:
                if not sensor_connections[id_val_index-1][j]:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload=str(values[i]))
                i += 1
            else:
                if not sensor_connections[id_val_index-1][j]:
                    CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val),
                                   payload=str(values[i]))
                    CLIENT.publish(topic=_TOPICS[i+1].format(id_val=id_val),
                                   payload=str(values[i+1]))
                i += 2
        CLIENT.publish(topic=_TOPICS[12].format(id_val=id_val),
                       payload=str(values[12]))
        publish_failed_sensors(id_val_index)


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


def map_board_ids(hardware_id):
    """
    Map the new hardware ids to the old integer id for compatibility with code.
    """
    global board_ids
    mapped_id = np.where(np.array(board_ids) == hardware_id)[0][0]
    return mapped_id + 1


def create_timestamp(tmstmp):
    """
    Returns given time returned by calling time.localtime()
    as a list.
    """
    return [tmstmp.tm_year, tmstmp.tm_mon,
            tmstmp.tm_mday, tmstmp.tm_hour,
            tmstmp.tm_min, tmstmp.tm_sec]


# ------------------------ constants and variables for the sensorboard --------
# Tuple with MQTT topics
_TOPICS = ("board{id_val}/co2_scd", "board{id_val}/co",
           "board{id_val}/o2", "board{id_val}/amb_press",
           "board{id_val}/temp1_am", "board{id_val}/humid1_am",
           "board{id_val}/temp2_am", "board{id_val}/humid2_am",
           "board{id_val}/temp3_am", "board{id_val}/humid3_am",
           "board{id_val}/temp4_am", "board{id_val}/humid4_am",
           "board{id_val}/rssi")
# Topic for the Sensorboardstatus
_Failed_times = "board{id_val}/active_status"
# Topic for the Sensorstatus
_Failed_sensor = "sensor{id_val}_stat_"
# Topic for broken limits
_Limits_broken = "board{id_val}/limits"

# Constants depending on the msg structure
number_of_sensors = 8
length_values = 13  # 8 sensors. Last 4 put out 2 values each + rssi

# Boolean for checking if the timer is done.
cb_timer_done = False

# Maximum of heartbeats that are allowed to be missed.
MAX_COUNT = 3

# board_ids based on the manuall numbering of the boards (to map to old ids)
board_ids = read_config()
sensorboard_list = dict()
for i in range(len(board_ids)):
    sensorboard_list[board_ids[i]] = 0

# packet counter for each board
packet_list = []
for i in range(len(board_ids)):
    packet_list.append([])

# counts the packets missed
packets_missed = dict()
for i in range(len(board_ids)):
    packets_missed[board_ids[i]] = 0

# counts retransmitted packets
retransmitted_packets = dict()
for i in range(len(board_ids)):
    retransmitted_packets[board_ids[i]] = 0

# Holds all values for the working/not working sensors.
connections = [0, 0, 0, 0, 0, 0, 0, 0]
sensor_connections = []
for i in range(len(board_ids)):
    sensor_connections.append(connections)

restarts = []
for i in range(len(board_ids)):
    restarts.append(0)

# Setting up MQTT
MQTT_SERVER = "192.168.30.17"
CLIENT = mqtt.Client()

# interval for checking if the board are working
timer_interval = 90

# receive parameters
MESSAGE_LENGTH = 72
_pkng_frmt = ">13f2H2I"

# package format for ack
_pkng_frmt_ack = ">2H3I"  # 16 bytes for ack

# ------------------------ general startup function calls ---------------------

# LoRa and MQTT Initialization
lora_init()
connect_mqtt()

# ------------------------ infinite loop execution ----------------------------
print("Receiving Packets......")
# Start of loop
threading.Timer(timer_interval, cb).start()
all_values = []
invalid_crcs = 0
while True:
    recv_msg, prssi = receive()
    if len(recv_msg) == MESSAGE_LENGTH:
        received_crc = struct.unpack(">L", recv_msg[-4:])[0]
        if received_crc != crc32(0, recv_msg[:-4], MESSAGE_LENGTH-4):
            print("Invalid CRC32 in msg")
            receiver_timestamp = time.localtime()
            rx_datetime = create_timestamp(receiver_timestamp)
            write_to_log_time("Invalid CRC32 in msg: ",
                              "N/A",
                              str(rx_datetime))
            invalid_crcs += 1
        else:
            # exclude timstamp and crc (8 bytes) to get msg
            values = struct.unpack(_pkng_frmt, recv_msg[:-8])
            id_received = values[16]
            packet_no_received = values[15]
            timestamp = list(struct.unpack(">L", recv_msg[-8:-4]))
            receiver_timestamp = time.localtime()
            rx_datetime = create_timestamp(receiver_timestamp)

            # send ACK
            send(str(id_received) + "," + str(timestamp[0]))

            # add heartbeat
            sensorboard_list[id_received] += 1

            old_id = map_board_ids(id_received) - 1
            if packet_no_received == 0 and len(packet_list[old_id]) != 0:
                packet_list[old_id] = []
                restarts[old_id] += 1

            # check if packet is a retransmission
            if packet_no_received in packet_list[old_id]:
                packet_list[old_id].remove(packet_no_received)
                retransmitted_packets[id_received] += 1
            packet_list[old_id].append(packet_no_received)

            # check if packets were lost
            packets_yet_received = len(packet_list[old_id]) - 1
            if packets_yet_received == packet_no_received:
                packets_missed[id_received] = 0
            elif packets_yet_received < packet_no_received:
                lost_packets = packet_no_received - packets_yet_received
                packets_missed[id_received] = lost_packets

            # save data for log and later visualization
            all_values += [values +
                           tuple(timestamp) +
                           tuple(rx_datetime) +
                           tuple([len(packet_list[old_id])]) +
                           tuple(retransmitted_packets) +
                           tuple(restarts) +
                           tuple([invalid_crcs])]
            write_to_log_time("Received ", str(timestamp[0]),
                              str(rx_datetime))

            value_list = list(values)

            # log for data and status data for later evaluation
            data = "D;" + str(value_list) + "\n"
            log_data(data)

            status_log = "S;" + str(id_received) + ";"
            status_log += str(packets_missed[id_received]) + ";"
            status_log += str(len(packet_list[old_id])) + ";"
            status_log += str(retransmitted_packets[id_received]) + ";"
            status_log += str(invalid_crcs) + "\n"
            log_data(status_log)

            # Round values to visualize the actual
            # data that goes to the backend
            for i in range(len(value_list)):
                if i <= 3:
                    value_list[i] = round(value_list[i], 2)
                elif i <= 11:
                    value_list[i] = round(value_list[i], 1)
            try:
                send_mqtt(value_list)
                print("Sent to MQTT")
                print(value_list,
                      timestamp,
                      create_timestamp(receiver_timestamp))
            except Exception:
                print("---------------- UNKOWN_BOARD_ID: " +
                      str(values[16]) + " ----------------")
    else:
        write_to_log_time(
            "Message that does no belong to the system: {}".format(
                len(recv_msg)), str(timestamp[0]), str(rx_datetime))

    # checks if any boards are not working
    if cb_timer_done:
        try:
            print("Invalid CRCs since last start: " + str(invalid_crcs))
            i = 0
            for each_board in list(sensorboard_list.keys()):
                print(str(each_board) + ":")
                old_board_id = map_board_ids(each_board)
                signal_count = sensorboard_list[each_board]
                print("packets received: " + str(len(packet_list[i])))
                print("packets missed: ",
                      packets_missed[each_board])
                print("packets retransmitted: ",
                      retransmitted_packets[each_board])
                print("restarts: ", restarts[i])
                if signal_count < 1:
                    print("Board {} not working".format(old_board_id))
                    CLIENT.publish(topic=_Failed_times.format(
                        id_val=old_board_id), payload="10000")
                else:
                    print("signal_count:", signal_count)
                    CLIENT.publish(topic=_Failed_times.format(
                        id_val=old_board_id), payload="1000")
                sensorboard_list[each_board] = 0
                i += 1
        except Exception as e:
            print(str(e))
        # store the values for visualization
        with open("sensor_values_raspbery.pkl", "wb") as f:
            pickle.dump(all_values, f)
        cb_timer_done = False
        threading.Timer(timer_interval, cb).start()
