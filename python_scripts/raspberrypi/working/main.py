# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika U.
# date: 07.09.2021
# function: Implentation of a LoRa receiving LoPy, which after receiving checks
#           if any of the received data is not valid. If any data is not valid
#           it wont be send via MQTT, otherwise it will.
# -------------------------------------------------------------------------------
import paho.mqtt.client as mqtt

import loralib as lora
import threading
import time
import struct

# Tuple with MQTT topics
_TOPICS = ("board{id_val}/co2_scd", "board{id_val}/co", "board{id_val}/o2", "board{id_val}/amb_press",
           "board{id_val}/temp1_am", "board{id_val}/humid1_am", "board{id_val}/temp2_am",
           "board{id_val}/humid2_am", "board{id_val}/temp3_am", "board{id_val}/humid3_am",
           "board{id_val}/temp4_am", "board{id_val}/humid4_am")

_Failed_times = "board{id_val}/active_status"
_Failed_sensor = "sensor{id_val}_stat_"
comp_const = 1
length_failed_sensors = 8
length_values = 12  # 12 sensor readings+sensor board number+heartbeat+limits broken
emergency = 13
heartbeat = 14
counter_board1 = 0
counter_board2 = 0
counter_board3 = 0
counter_board4 = 0
val_hb = 0

MAX_COUNT = 2

sensor_connections = [[0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0]]

#global counter_mqtt
counter_mqtt = 0

# Setting up MQTT
MQTT_SERVER = '192.168.30.17'
CLIENT = mqtt.Client()

# Callback function to trace heartbeat packet loss

            
def lora_init():
    """
    """
    lora.init(868000000, 7)

        
def receive():
    """
    """
    lora.changemode(1)
    while True:
        msg = lora.recv()[0]
        if msg:
            return msg
            break

                    
def send(msg):
    """
    """
    lora.changemode(0)
    if isinstance(msg, str):
        msg = msg.encode()
    lora.send(msg)

        
def connect_mqtt():
    """
    """
    try:
        CLIENT.connect(MQTT_SERVER)
    except:
        pass


def cb():
    """
    """
    global counter_board1, counter_board2, counter_board3, counter_board4
    counter_board1 += 1
    if counter_board1 == MAX_COUNT:
        CLIENT.publish(topic=_Failed_times.format(id_val=1), payload="1")
    counter_board2 += 1
    if counter_board2 == MAX_COUNT:
        CLIENT.publish(topic=_Failed_times.format(id_val=2), payload="1")
    counter_board3 += 1
    if counter_board3 == MAX_COUNT:
        CLIENT.publish(topic=_Failed_times.format(id_val=3), payload="1")
    counter_board4 += 1
    if counter_board4 == MAX_COUNT:
        CLIENT.publish(topic=_Failed_times.format(id_val=4), payload="1")


def publish_failed_sensors(id_val):
    """
    """
    for i in range(length_failed_sensors):
        CLIENT.publish(topic=_Failed_sensor.format(id_val=id_val) + str(i),
                       payload=str(sensor_connections[id_val][i]))


def check_sensors(val, id_val):
    """
    """
    for i in range(length_failed_sensors):
        if val & comp_const:
            sensor_connections[id_val][i] = 1
            val = val >> comp_const
        else:
            sensor_connections[id_val][i] = 0
            val = val >> comp_const


def send_mqtt(values):
    """
    """
    connect_mqtt()
    global counter_mqtt
    id_val = str(values[15])
    if not values[length_values]:
        for j in range(length_values):
            try:
                CLIENT.publish(topic=_TOPICS[j].format(id_val=id_val), payload=str(values[j]))
            except:
                pass
    else:
        check_sensors(values[length_values])
        i = 0
        for j in range(length_failed_sensors):
            if i < 4:
                if not sensor_connections[id_val-1][j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload=str(values[i]))
                    except:
                        pass
                i += 1
            else:
                if not sensor_connections[id_val-1][j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i].format(id_val=id_val), payload=str(values[i]))
                        CLIENT.publish(topic=_TOPICS[i+1].format(id_val=id_val), payload=str(values[i+1]))
                    except:
                        pass
                i += 2
        publish_failed_sensors(id_val)


def timer_start():
    """
    """
    cb()
    threading.Timer(3.5, timer_start).start()

# Connect WIFI and MQTT

lora_init()
connect_mqtt()
timer_start()

# Start of loop
while True:
    recv_msg = receive()
    try:
        values = struct.unpack('ffffffffffffIIII', recv_msg)
        #Converting to list to obtain float subsitute
        l = list(values)
        for i in range(len(l)):
            if i <= 3:
                l[i] = round(l[i], 2)
            elif i <= 11:
                l[i] = round(l[i], 1)              
        print(l)
        # prevent spikes         
        if l[0] > 40000 or l[0] < 0 or l[1] > 1000 or l[1] < 0 or l[2] > 25 or l[2] < 0 or l[3] > 1100 or l[3] < 300 or l[4] > 80 or l[4] < -40 or l[5] > 100 or l[5] < 0 or l[6] > 80 or l[6] < -40 or l[7] > 100 or l[7] < 0 or l[8] > 80 or l[8] < -40 or l[9] > 100 or l[9] < 0 or l[10] > 80 or l[10] < -40 or l[11] > 100 or l[11] < 0 or l[12] > 255 or l[12] < 0 or l[13] < 0 or l[13] > 1 or l[15] > 4 or l[15] < 1:
            time.sleep(0.05)  # OPTIMIZE! 
            send(str(l[15]))
            print("SEND")
        else:
            send_mqtt(l)
            time.sleep(0.05)  # OPTIMIZE! 
            send(str(l[15]))
            print("SEND")

    except:
        try:
            val_hb = struct.unpack('I', recv_msg)[0]
            print(val_hb)
            if val_hb == 1:
                counter_board1 = 0
                CLIENT.publish(topic=_Failed_times.format(id_val=1), payload="0")
            elif val_hb == 2:
                counter_board2 = 0
                CLIENT.publish(topic=_Failed_times.format(id_val=2), payload="0")
            elif val_hb == 3:
                counter_board3 = 0
                CLIENT.publish(topic=_Failed_times.format(id_val=3), payload="0")
            elif val_hb == 4:
                counter_board4 = 0
                CLIENT.publish(topic=_Failed_times.format(id_val=4), payload="0")
        except:
            pass



