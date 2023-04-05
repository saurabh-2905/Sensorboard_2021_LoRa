# ------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika Unnikrishnan, Saurabh Band
# date: 15.02.2023
# function: Central LoRa receiver. Pushes data via MQTT to the Backend.
# -------------------------------------------------------------------------------

# from gui import PBR_Control

import paho.mqtt.client as mqtt

import loralib as lora
import threading
import time
import struct
import numpy as np
import pickle

# ------------------------ function declaration -------------------------------


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


def write_to_log_time(msg, timestamp, rx_timestamp):
    """
    Write a given Message to the file log.txt.
    """
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + timestamp + "\t" + rx_timestamp + "\n")


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
        write_to_log_time(str(em), "0", "0")


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


def send_mqtt(values, prssi):
    """
    Sends given values to the MQTT Server. Also publishes information
    about working and not working sensors, given by :function: check_sensors.
    """
    connect_mqtt()
    CLIENT.publish(topic=_PRSSI_rbpi, payload=str(prssi))
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


def send_cmd(sema1):
    """
    """
    # read data from file while resources are locked
    sema1.acquire()
    try:
        with open("temp", "r") as f:
            new_values = f.read()
    except Exception:
        sema1.release()
    sema1.release()
    new_values = new_values.split(";")
    pump_nr = float(new_values[4][4])
    pump_amount = float(new_values[5])
    tvs_send = [float(new_values[0]), float(new_values[1]),
                float(new_values[2]), float(new_values[3])]
    tv_msg = struct.pack(pbr_ack_decoding, 1, pump_nr, pump_amount,
                         tvs_send[0], tvs_send[1], tvs_send[2],
                         tvs_send[3], 0, PBR_ID)
    tv_msg += struct.pack(">L", crc32(0, tv_msg, 34))
    send(tv_msg)
    sema1.acquire()
    with open("temp", "w") as f:
        f.write("-1.0;-1.0;-1.0;-1.0;pump0;-1.0;")
    sema1.release()


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

# Topic for PRSSI value
_PRSSI_rbpi = "lora_router_prssi"

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

# packet list for each board
packet_list = []
for i in range(len(board_ids)):
    packet_list.append([])

# packet counter for each board
packet_counter = []
for i in range(len(board_ids)):
    packet_counter.append(0)

# Holds all values for the working/not working sensors.
connections = [0, 0, 0, 0, 0, 0, 0, 0]
sensor_connections = []
for i in range(len(board_ids)):
    sensor_connections.append(connections)

# Setting up MQTT
MQTT_SERVER = "192.168.30.17"
CLIENT = mqtt.Client()

# interval for checking if the board are working
timer_interval = 90

# receive parameters
MESSAGE_LENGTH = 76  # length of messages received from boards
_pkng_frmt = ">13f2H2I"  # packet format without timestamp and crc (2L)

# init start values
invalid_crcs = 0
no_retr = True
# ------------------------ general startup function calls ---------------------

# LoRa and MQTT Initialization
lora_init()
connect_mqtt()

# ------------------------ infinite loop execution ----------------------------
print("Receiving Packets......")
# Start of loop
threading.Timer(timer_interval, cb).start()
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
            values = struct.unpack(_pkng_frmt, recv_msg[:-12])
            id_received = values[16]
            packet_no_received = values[15]
            timestamp_retr = list(struct.unpack(">L", recv_msg[-8:-4]))[0]
            timestamp_sent = list(struct.unpack(">L", recv_msg[-12:-8]))[0]
            
            # create timestampt with receiving time
            receiver_timestamp = time.localtime()
            rx_datetime = create_timestamp(receiver_timestamp)

            # create old_id, which is the ID from a sensorboard converted
            # to a number defined in the config file (0 to 6)
            old_id = map_board_ids(id_received)-1

            # send ACK
            send(str(id_received) + "," + str(timestamp_sent))

            # reset value for indicating a retransmissitted message
            no_retr = True

            # check if the received packet is coherent with the
            # before received packets
            if packet_no_received == 0:
                packet_counter[old_id] = packet_no_received
            elif packet_no_received > packet_counter[old_id]:
                packet_counter[old_id] = packet_no_received
            else:
                no_retr = False

            # add heartbeat
            sensorboard_list[id_received] += 1

            packet_list[old_id].append((values, id_received, packet_no_received,
                                        prssi, timestamp_sent, timestamp_retr,
                                        rx_datetime))

            # write all data to a pickle file for later processing
            with open("log_sensorboards.pkl", "wb") as f:
                pickle.dump(packet_list, f)

            value_list = list(values)

            # Round values to visualize the actual
            # data that is send to the backend
            for i in range(len(value_list)):
                if i <= 3:
                    value_list[i] = round(value_list[i], 2)
                elif i <= 11:
                    value_list[i] = round(value_list[i], 1)
            try:
                if no_retr:
                    #send_mqtt(value_list, prssi)
                    print("Sent to MQTT")
                else:
                    print("retransmission, not sent to mqtt")
                print(value_list, timestamp_sent, rx_datetime)
            except Exception as e:
                print(str(e))
                print("---------------- UNKOWN_BOARD_ID: " +
                      str(values[16]) + " ----------------")
    else:
        try:
            print("Messsage not belonging to the system with length: "
                  + str(len(recv_msg)))
        except Exception:
            pass

    # checks if any boards are not working
    if cb_timer_done:
        try:
            print("------ status message START ------")
            print("Invalid CRCs since last start: " + str(invalid_crcs))
            i = 0

            # checks if any board stopped working
            for each_board in list(sensorboard_list.keys()):
                print("Board with ID " + str(each_board) + ":")
                old_board_id = map_board_ids(each_board)
                signal_count = sensorboard_list[each_board]
                if signal_count < 1:
                    print("Board not working")
                    #CLIENT.publish(topic=_Failed_times.format(
                    #    id_val=old_board_id), payload="10000")
                else:
                    print("signal_count:", signal_count)
                    #CLIENT.publish(topic=_Failed_times.format(
                    #    id_val=old_board_id), payload="1000")
                sensorboard_list[each_board] = 0
                i += 1
        except Exception as e:
            print(str(e))
        cb_timer_done = False
        threading.Timer(timer_interval, cb).start()
        print("------ status message END ------")