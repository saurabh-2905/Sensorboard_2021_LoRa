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

import socket, ustruct, ubinascii, network, machine, time

# Tuple with MQTT topics
_TOPICS = ("board1/co2_scd", "board1/co", "board1/o2", "board1/amb_press",
           "board1/temp1_am", "board1/humid1_am", "board1/temp2_am",
           "board1/humid2_am", "board1/temp3_am", "board1/humid3_am",
           "board1/temp4_am", "board1/humid4_am")

_Failed_times = "board1/failed"
comp_const = const(1)
length_failed_sensors = const(8)
length_values = const(12) #12 sensor readings+sensor board number+heartbeat+limits broken
emergency = const(13)
heartbeat = const(14)

sensor_connections = [0, 0, 0, 0, 0, 0, 0, 0]

counter = 0
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
    global counter
    counter += 1
    if counter == 3:
        CLIENT.publish()# TODO

def connect_wifi_mqtt(ssid="Mamba", pw="We8r21u7"):
    """
    """
    wlan.connect(ssid=ssid, auth=(network.WLAN.WPA2, pw))
    time.sleep(10)
    try:
        CLIENT.connect()
    except:
        print("error")


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
    if not values[length_values]:
        for j in range(length_values):
            try:
                CLIENT.publish(topic=_TOPICS[j], msg=str(values[j]))
                CLIENT.publish(topic=_Failed_times, msg=str(counter_mqtt))
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
                        CLIENT.publish(topic=_TOPICS[i], msg=str(values[i]))
                        CLIENT.publish(topic=_Failed_times, msg=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                        
                    i += 1
            else:
                if not sensor_connections[j]:
                    try:
                        CLIENT.publish(topic=_TOPICS[i], msg=str(values[i]))
                        CLIENT.publish(topic=_TOPICS[i+1], msg=str(values[i+1]))
                        CLIENT.publish(topic=_Failed_times, msg=str(counter_mqtt))
                        counter_mqtt = 0
                    except:
                        counter_mqtt += 1
                i += 2
    publish_failed_sensors()


# Connect WIFI and MQTT
connect_wifi_mqtt()

# Check if the connection is established
if not wlan.isconnected():
    connect_wifi_mqtt()

timer1 = Timer(1)
timer1.init(period=2000, mode=Timer.PERIODIC, callback=cb)

timer1 = Timer.Alarm(handler=cb, periodic=True)

# Start of loop
while True:
    recv_msg = s.recv(64)
    if wlan.isconnected():
        values = ustruct.unpack('ffffffffffffIIII', recv_msg)
        #If limits are broken send immediately
        if values[emergency] and (not values[heartbeat]):
            send_mqtt(values)
        elif values[heartbeat]:
            counter = 0
    else:
        connect_wifi_mqtt()
