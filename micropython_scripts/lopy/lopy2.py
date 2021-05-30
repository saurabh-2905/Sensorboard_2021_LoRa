#-------------------------------------------------------------------------------
# author: Florian Stechmann, Malavika U.
# date: 30.05.2020
# function: Implentation of a LoRa receiving LoPy, which after receiving checks
#           if any of the received data is not valid. If any data is not valid
#           it wont be send via MQTT, otherwise it will.
#-------------------------------------------------------------------------------
from network import LoRa
from network import WLAN
from umqtt import MQTTClient

import socket, ustruct, ubinascii

# Tuple with MQTT topics
_TOPICS = ("board2/co2_scd", "board2/co", "board2/o2", "board2/amb_press", "board2/temp1_am", "board2/humid1_am", "board2/temp2_am", "board2/humid2_am", "board2/temp3_am", "board2/humid3_am", "board2/temp4_am", "board2/humid4_am")

length_topics = const(14)
comp_const = const(1)

sensor_connections = [0, 0, 0, 0, 0, 0, 0, 0]
wifi_connection = 1

# Setting up WIFI
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Setting up MQTT 
MQTT_SERVER = '192.168.30.17'    
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
CLIENT = MQTTClient(CLIENT_ID, MQTT_SERVER)

# Setting up LoRa
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ, sf=7,
            preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON,
            tx_iq=False, rx_iq=False, public=True)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(True)

def connect_wifi_mqtt(ssid="Mamba", pw="We8r21u7"):
    """
    """
    wlan.connect(ssid, pw)
    CLIENT.connect()      

def check_wifi():
    """
    """
    if wlan.isconnected():
        wifi_connection = 1
        return True
    else:
        wifi_connection = 0
        return False
    
def set_failed_sensor(number):
    """
    """
    sensor_connections[number-1] = 1

def check_sensors(val):
    """
    """
    for i in range(8):
        if val & comp_const == 1:
            set_failed_sensor[i] == 1
        val = val >> comp_const
    
def send_mqtt(values):
    """
    """
    if values[length_topics] == 0:
        for j in range(12):
            CLIENT.publish(topic=_TOPICS[j], msg=values[j])
    else:
        check_sensors(values)
        for i in range(12):
            if i < 4:
                if sensor_connections[i] == 0:
                    CLIENT.publish(topic=_TOPICS[i], msg=values[i])
            else:
                if sensor_connections[i] == 0 and i % 2 == 0:
                    CLIENT.publish(topic=_TOPICS[i], msg=values[i])
                    CLIENT.publish(topic=_TOPICS[i+1], msg=values[i+1])
                    

# Connect WIFI and MQTT
connect_wifi_mqtt()

# Check if the connection is established
if not check_wifi():
    connect_wifi_mqtt()
    
# Start of loop
while True:
    recv_msg = s.recv(64)
    if check_wifi_mqtt():
        values = ustruct.unpack('ffffffffffffffI', raw_values)
        send_mqtt(values)
    else:
        connect_wifi_mqtt()
