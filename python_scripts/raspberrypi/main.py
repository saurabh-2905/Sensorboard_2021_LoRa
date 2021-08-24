# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika U.
# date: 30.05.2020
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
_TOPICS = ("board{id}/co2_scd", "board{id}/co", "board{id}/o2", "board{id}/amb_press",
           "board{id}/temp1_am", "board{id}/humid1_am", "board{id}/temp2_am",
           "board{id}/humid2_am", "board{id}/temp3_am", "board{id}/humid3_am",
           "board{id}/temp4_am", "board{id}/humid4_am")

_Failed_times = "board{id}/active_status"
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

sensor_connections = [0, 0, 0, 0, 0, 0, 0, 0]

#global counter_mqtt
counter_mqtt = 0

# Setting up MQTT
MQTT_SERVER = '192.168.30.17'
CLIENT = mqtt.Client()

# Callback function to trace heartbeat packet loss


def cb():
    """
    """
    global counter_board1, counter_board2, counter_board3, counter_board4
    if val_hb == 1:
        counter_board1 += 1
        if counter_board1 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=1), payload="1")
    elif val_hb == 2:
        counter_board2 += 1
        if counter_board2 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=2), payload="1")
    elif val_hb == 3:
        counter_board3 += 1
        if counter_board3 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=3), payload="1")
    elif val_hb == 4:
        counter_board4 += 1
        if counter_board4 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=4), payload="1")

            
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


def set_failed_sensor(number, val):
    """
    """
    sensor_connections[number] = val


def publish_failed_sensors():
    """
    """
    for i in range(length_failed_sensors):
        CLIENT.publish(topic="sensor1_stat_" + str(i),
                       payload=str(sensor_connections[i]))


def check_sensors(val):
    """
    """
    for i in range(length_failed_sensors):
        if val & comp_const:
            set_failed_sensor(i, 1)
        else:
            set_failed_sensor(i, 0)
        val = val >> comp_const


def send_mqtt(values):
    """
    """
    connect_mqtt()
    global counter_mqtt
    id = str(values[15])
    if not values[length_values]:
        for j in range(length_values):
            try:
                CLIENT.publish(topic=_TOPICS[j].format(id=id), payload=str(values[j]))
                CLIENT.publish(topic=_Failed_times.format(id=id), payload=str(counter_mqtt))
                counter_mqtt = 0
            except:
                counter_mqtt += 1
    else:
        check_sensors(values[length_values])
        i = 0
        for j in range(length_failed_sensors):
            if i < 4:
                if not sensor_connections[j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i].format(id=id), payload=str(values[i]))
                        CLIENT.publish(topic=_Failed_times.format(id=id), payload=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                        pass
                    i += 1
            else:
                if not sensor_connections[j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i].format(id=id), payload=str(values[i]))
                        CLIENT.publish(topic=_TOPICS[i+1].format(id=id), payload=str(values[i+1]))
                        CLIENT.publish(topic=_Failed_times.format(id=id), payload=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                        pass
                i += 2
    publish_failed_sensors()


def timer_start():
    """
    """
    cb()
    threading.Timer(2, timer_start).start()

# Connect WIFI and MQTT

lora_init()
connect_mqtt()
timer_start()

# Start of loop
while True:
    recv_msg = receive()
    try:
        values = struct.unpack('ffffffffffffIIII', recv_msg)
        print(values)
        send_mqtt(values)
        if not values[emergency]:
            time.sleep(0.05)  # OPTIMIZE! 
            send(str(values[15]))
            print("SEND")
    except:
        try:
            val_hb = struct.unpack('I', recv_msg)[0]
            print(val_hb)
            if val_hb == 1:
                counter_board1 = 0
                CLIENT.publish(topic=_Failed_times.format(id=1), payload="0")
            elif val_hb == 2:
                counter_board2 = 0
                CLIENT.publish(topic=_Failed_times.format(id=2), payload="0")
            elif val_hb == 3:
                counter_board3 = 0
                CLIENT.publish(topic=_Failed_times.format(id=3), payload="0")
            elif val_hb == 4:
                counter_board4 = 0
                CLIENT.publish(topic=_Failed_times.format(id=4), payload="0")
        except:
            pass
