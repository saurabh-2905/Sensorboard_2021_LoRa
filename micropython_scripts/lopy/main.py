# -------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika U.
# date: 30.05.2020
# function: Implentation of a LoRa receiving LoPy, which after receiving checks
#           if any of the received data is not valid. If any data is not valid
#           it wont be send via MQTT, otherwise it will.
# -------------------------------------------------------------------------------
from network import LoRa
from mqtt import MQTTClient
from machine import Timer

import socket, ustruct, ubinascii, network, machine, time, micropython

# Tuple with MQTT topics
_TOPICS = ("board{id}/co2_scd", "board{id}/co", "board{id}/o2", "board{id}/amb_press",
           "board{id}/temp1_am", "board{id}/humid1_am", "board{id}/temp2_am",
           "board{id}/humid2_am", "board{id}/temp3_am", "board{id}/humid3_am",
           "board{id}/temp4_am", "board{id}/humid4_am")

_Failed_times = "board{id}/active_status"
comp_const = const(1)
length_failed_sensors = const(8)
length_values = const(12) #12 sensor readings+sensor board number+heartbeat+limits broken
emergency = const(13)
heartbeat = const(14)
counter_board1 = 0
counter_board2 = 0
counter_board3 = 0
counter_board4 = 0
val_hb = 0

sensor_connections = [0, 0, 0, 0, 0, 0, 0, 0]

micropython.alloc_emergency_exception_buf(100)

#global counter_mqtt
counter_mqtt = 0

# Setting up WIFI
wlan = network.WLAN(mode=network.WLAN.STA)

# Setting up MQTT
MQTT_SERVER = '192.168.30.17'
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
CLIENT = MQTTClient(client_id=CLIENT_ID, server=MQTT_SERVER, port=1883)

# Setting up LoRa
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ, sf=7,
            preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON,
            tx_iq=False, rx_iq=False, public=True)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(True)

#Callback function to trace heartbeat packet loss
def cb(p):
    global counter_board1, counter_board2, counter_board3, counter_board4
    if val_hb == 1:
        counter_board1 += 1
        if counter_board1 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=1), msg="1")
    elif val_hb == 2:
        counter_board2 += 1
        if counter_board2 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=2), msg="1")
    elif val_hb == 3:
        counter_board3 += 1
        if counter_board3 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=3), msg="1")
    elif val_hb == 4:
        counter_board4 += 1
        if counter_board4 == 3:
            CLIENT.publish(topic=_Failed_times.format(id=4), msg="1")


def connect_wifi_mqtt(ssid="Mamba", pw="We8r21u7"):
    """
    """
    wlan.connect(ssid=ssid, auth=(network.WLAN.WPA2, pw))
    time.sleep(10)
    try:
        CLIENT.connect()
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
                       msg=str(sensor_connections[i]))


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
    global counter_mqtt
    id = str(values[15])
    if not values[length_values]:
        for j in range(length_values):
            try:
                CLIENT.publish(topic=_TOPICS[j].format(id=id), msg=str(values[j]))
                CLIENT.publish(topic=_Failed_times.format(id=id), msg=str(counter_mqtt))
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
                        CLIENT.publish(topic=_TOPICS[i].format(id=id), msg=str(values[i]))
                        CLIENT.publish(topic=_Failed_times.format(id=id), msg=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                        pass
                    i += 1
            else:
                if not sensor_connections[j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i].format(id=id), msg=str(values[i]))
                        CLIENT.publish(topic=_TOPICS[i+1].format(id=id), msg=str(values[i+1]))
                        CLIENT.publish(topic=_Failed_times.format(id=id), msg=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                        pass
                i += 2
    publish_failed_sensors()

# Connect WIFI and MQTT
connect_wifi_mqtt()

# Check if the connection is established
if not wlan.isconnected():
    connect_wifi_mqtt()

Timer.Alarm(cb, 2.0, periodic=True)

# Start of loop
while True:
    recv_msg = s.recv(64)
    if wlan.isconnected():
        try:
            values = ustruct.unpack('ffffffffffffIIII', recv_msg)
            print(values)
            send_mqtt(values)
            if not values[emergency]:
                s.send(str(values[15])) 
        except:
            try:
                val_hb = ustruct.unpack('I', recv_msg)[0]
                if val_hb == 1:
                    counter_board1 = 0
                    CLIENT.publish(topic=_Failed_times.format(id=1), msg="0")
                elif val_hb == 2:
                    counter_board2 = 0
                    CLIENT.publish(topic=_Failed_times.format(id=2), msg="0") 
                elif val_hb == 3:
                    counter_board3 = 0
                    CLIENT.publish(topic=_Failed_times.format(id=3), msg="0") 
                elif val_hb == 4:
                    counter_board4 = 0
                    CLIENT.publish(topic=_Failed_times.format(id=4), msg="0")
            except:
                pass
    else:
        connect_wifi_mqtt()
