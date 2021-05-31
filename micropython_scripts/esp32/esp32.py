
#import libraries
from machine import Pin, SPI, I2C
import network, ubinascii, ustruct
from umqtt.robust import MQTTClient
from scd30 import SCD30
from mcp3221 import MCP3221
from bmp180 import BMP180
from am2301 import AM2301


# #setting IP address of MQTT broker server and enabling WLAN object & setting machine ID of MCU
# wlan = network.WLAN(network.STA)
# MQTT_SERVER = '192.168.30.17'
# CLIENT_ID = ubinascii.hexlify(machine.unique_id())

#addresses of sensors
O2_ADRR = 0x48
CO_ADRR = 0x49
SCD30_ADRR = 0x61
AM2301_1_ADRR = 0
AM2301_2_ADRR = 4
AM2301_3_ADRR = 17
AM2301_4_ADRR = 16

#Connection_variables initialisation
# CONNECTION_LORA = 1
# CONNECTION_MQTT = 1
CONNECTION_CO2 = 1
CONNECTION_CO = 1
CONNECTION_O2 = 1
CONNECTION_BMP = 1
CONNECTION_A1 = 1
CONNECTION_A2 = 1
CONNECTION_A3 = 1
CONNECTION_A4 = 1
scd_co2 = 0
scd_temp = 0
scd_hum = 0

#establish SPI Bus
#doubt on spi _id -> 1 or 2 refer refe for esp32 micropython
try:
    SPI_BUS = SPI(2, baudrate=10000000, sck=Pin(18, Pin.OUT), miso=Pin(19, Pin.IN), mosi=Pin(23, Pin.OUT)) #used 2 as first argument not 1
    SPI_BUS.init() #why required ?
    lora_sender = LoRa(SPI_BUS, True, cs=Pin(5, Pin.IN), rx=Pin(2, Pin.IN)) #diff pins specified in sx1276 datasheet
except:
    CONNECTION_LORA = 0

#establish I2c Bus
try:
    I2C_BUS = I2C(1, sda=Pin(21, Pin.IN), scl= Pin(22, Pin.IN), freq=100000) #freq diff from docu, make any change ?, Pin.IN & Pin.OUT mentioned not in code(of Flo)
except:
    raise #set conn_variables to sensors zero ?

# #creating mqtt object
# try:
#     CLIENT = MQTTClient(CLIENT_ID, MQTT_SERVER)
# except:
#     raise

#creating sensor objects try except method

try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except:
    CONNECTION_CO2 = 0

try:
    MCP_CO = MCP3221(I2CBUS, CO_ADRR)
except:
    CONNECTION_CO = 0

try:
    MCP_O2 = MCP3221(I2CBUS, O2_ADRR)
except:
    CONNECTION_O2 = 0

try:
    BMP = BMP180(I2CBUS)
except:
    CONNECTION_BMP = 0

try:
    AM2301_1 = AM2301(AM2301_1_ADRR)
except:
    CONNECTION_A1 = 0

try:
    AM2301_2 = AM2301(AM2301_2_ADRR)
except:
    CONNECTION_A2 = 0

try:
    AM2301_3 = AM2301(AM2301_3_ADRR)
except:
    CONNECTION_A3 = 0

try:
    AM2301_4 = AM2301(AM2301_4_ADRR)
except:
    CONNECTION_A4 = 0

# #Wlan connection function
# def wlan_connect():
#     try:
#         if not wlan.isconnected():
#             wlan.active(True)
#             wlan.connect(essid='Mamba', password='We8r21u7')
#             if wlan.isconnected():
#                 pass
#     except:
#         pass
#
# #mqtt broker connection function
# def mqtt_connect():
#     try:
#         CLIENT.connect() #eliminated CONNECTION_MQTT =1 again.
#     except:
#         CONNECTION_MQTT = 0

#measure data from sensor try except method

def measure_scd30():
    """
    Takes CO2 reading
    """
    if scd30.get_status_ready() == 1:

        return scd30.read_measurement()

    else:
        return []

def measure_co():
    """
    Takes CO reading
    """
    return mcp_co.read_measurement_co()

def measure_o2():
    """
    Takes O2 reading
    """
    return mcp_o2.read_measurement_o2()

def measure_bmp():
    """
    Takes pressure reading
    """
    return bmp180.pressure/100

def measure_am1():
    """
    Temp & humidity sensor 1 reading
    """
    return am2301_1.read_measurement()

def measure_am2():
    """
    Temp & humidity sensor 2 reading
    """
    return am2301_2.read_measurement()

def measure_am3():
    """
    Temp & humidity sensor 3 reading
    """
    return am2301_3.read_measurement()

def measure_am4():
    """
    Temp & humidity sensor 4 reading
    """
    return am2301_4.read_measurement()

# Measure & check Sensor reading
def measure(conn_status,func,sensor_id):

    try:
        return func()
    except:
        raise

#infinite loop execution
while True:
    #
    # mqtt_connect()
    # wlan_connect()

    CONNECTION_VAR = [CONNECTION_CO2, CONNECTION_CO, CONNECTION_O2, CONNECTION_BMP, CONNECTION_A1, CONNECTION_A2, CONNECTION_A3, CONNECTION_A4]
    FUNC_VAR = [measure_scd30, measure_co, measure_o2, measure_bmp, measure_a1, measure_a2, measure_a3, measure_a4]
    SENSOR_DATA = []
    FAIL_STATUS = 0b00000000
    SENSOR_STATUS = 0b00000000

    for i in range(len(CONNECTION_VAR)):

        if CONNECTION_VAR[i]:
            #CO
            """
            Sensor Data is available & sensor is working
            """
            func_call = FUNC_VAR[i]

            try:
                if i == 0:
                    """
                    SCD30 sensor readings(involves three values)
                    """
                    scd_co2, scd_temp, scd_hum = measure(CONNECTION_VAR[i], func_call, i)
                    SENSOR_DATA.extend((round(scd_co2, 2), round(scd_temp, 2), round(scd_hum, 2)))

                elif  i<4 and i>0:
                    """
                    MCP3221, BMP180 sensor reading
                    """
                    SENSOR_DATA.append(round(measure(CONNECTION_VAR[i], func_call, i), 2))

                else:
                    """
                    AM2301 readings(involves 2 values)
                    """
                    am_temp, am_hum = measure(CONNECTION_VAR[i], func_call, i)
                    SENSOR_DATA.extend((round(am_temp, 2), round(am_hum, 2)))

            except:
                CONNECTION_VAR[i] = 0

        elif not CONNECTION_VAR[i]:
            """
            Sensor failed
            """
            if i == 0:
                SENSOR_DATA.extend((0,0,0)) #SCD30 involves three readings
                FAIL_STATUS |= 1
                SENSOR_STATUS = FAIL_STATUS

            elif i<4 and i>0:
                SENSOR_DATA.append(0) #Sensors other than SCD30
                FAIL_STATUS = 1<<i
                SENSOR_STATUS |= FAIL_STATUS

            else:
                SENSOR_DATA.extend((0,0)) #Sensors other than SCD30
                FAIL_STATUS = 1<<i
                SENSOR_STATUS |= FAIL_STATUS

    msg = ustruct.pack('ffffffffffffffI', *SENSOR_DATA, SENSOR_STATUS)
    lora_sender.send(msg)













#connect to WLAN func call


#connect to mqtt func call
