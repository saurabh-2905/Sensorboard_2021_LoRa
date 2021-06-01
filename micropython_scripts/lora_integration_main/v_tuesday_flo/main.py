# -------------------------------------------------------------------------------
# author: Malavika U, Florian Stechmann
# date: 31.05.2020
# function:
# -------------------------------------------------------------------------------

# import libraries
from machine import Pin, I2C, SPI
import ustruct
from mcp3221 import MCP3221
from scd30 import SCD30
from bmp180 import BMP180
from am2301 import AM2301
from lora import LoRa

# addresses of sensors
O2_ADDR = const(0x48)
CO_ADDR = const(0x49)
SCD30_ADDR = const(0x61)
AM2301_1_ADDR = const(0)
AM2301_2_ADDR = const(4)
AM2301_3_ADDR = const(17)
AM2301_4_ADDR = const(16)

# Connection_variables initialisation
FAILED_LORA = 1
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
am_temp = 0  # did not previously initialise this variable
am_hum = 0  # did not previously initialise this variable

# establish I2c Bus
try:
    I2CBUS = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
except:
    raise

# SPI Bus initialsierung
try:
    SPI_BUS = SPI(1, baudrate=10000000, sck=Pin(18, Pin.OUT),
                  mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    SPI_BUS.init()
    lora_sender = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except:
    FAILED_LORA = 0

try:
    scd30 = SCD30(I2CBUS, SCD30_ADDR)
    scd30.start_continous_measurement()
except:
    CONNECTION_CO2 = 0

try:
    MCP_CO = MCP3221(I2CBUS, CO_ADDR)
except:
    CONNECTION_CO = 0

try:
    MCP_O2 = MCP3221(I2CBUS, O2_ADDR)
except:
    CONNECTION_O2 = 0

try:
    BMP = BMP180(I2CBUS)
except:
    CONNECTION_BMP = 0

try:
    AM2301_1 = AM2301(AM2301_1_ADDR)
except:
    CONNECTION_A1 = 0

try:
    AM2301_2 = AM2301(AM2301_2_ADDR)
except:
    CONNECTION_A2 = 0

try:
    AM2301_3 = AM2301(AM2301_3_ADDR)
except:
    CONNECTION_A3 = 0

try:
    AM2301_4 = AM2301(AM2301_4_ADDR)
except:
    CONNECTION_A4 = 0


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
    return MCP_CO.read_measurement_co()


def measure_o2():
    """
    Takes O2 reading
    """
    return MCP_O2.read_measurement_o2()


def measure_bmp():
    """
    Takes pressure reading
    """
    return BMP.pressure/100


def measure_am1():
    """
    Temp & humidity sensor 1 reading
    """
    return AM2301_1.read_measurement()


def measure_am2():
    """
    Temp & humidity sensor 2 reading
    """
    return AM2301_2.read_measurement()


def measure_am3():
    """
    Temp & humidity sensor 3 reading
    """
    return AM2301_3.read_measurement()


def measure_am4():
    """
    Temp & humidity sensor 4 reading
    """
    return AM2301_4.read_measurement()


CONNECTION_VAR = [1, 1, 1, 1, 1, 1, 1, 1]
FUNC_VAR = (measure_scd30, measure_co, measure_o2, measure_bmp,
            measure_am1, measure_am2, measure_am3, measure_am4)

# infinite loop execution
while True:
    FAIL_STATUS = 0
    SENSOR_STATUS = 0
    SENSOR_DATA = []
    for i in range(len(CONNECTION_VAR)):
        if CONNECTION_VAR[i]:
            # Sensor Data is available & sensor is working
            func_call = FUNC_VAR[i]
            try:
                if i == 0:
                    # SCD30 sensor readings(involves three values)
                    scd_co2, scd_temp, scd_hum = func_call()
                    SENSOR_DATA.extend((round(scd_co2, 2),
                                        round(scd_temp, 2), round(scd_hum, 2)))
                elif 1 <= i <= 3:  # made small condition change
                    # MCP3221, BMP180 sensor reading
                    SENSOR_DATA.append(round(func_call(), 2))
                else:
                    # AM2301 readings(involves 2 values)
                    am_temp, am_hum = func_call()
                    SENSOR_DATA.extend((round(am_temp, 2), round(am_hum, 2)))
            except:
                CONNECTION_VAR[i] = 0
        if not CONNECTION_VAR[i]:
            # Sensor failed
            if i == 0:
                SENSOR_DATA.extend((0, 0, 0))  # SCD30 involves three readings
                FAIL_STATUS |= 1
                SENSOR_STATUS = FAIL_STATUS
            elif 1 <= i <= 3:
                SENSOR_DATA.append(0)  # Sensors other than SCD30
                FAIL_STATUS = 1 << i
                SENSOR_STATUS += FAIL_STATUS  # changed the 'bitwise or' to + operation
            else:
                SENSOR_DATA.extend((0,0))  # Sensors other than SCD30
                FAIL_STATUS = 1 << i
                SENSOR_STATUS += FAIL_STATUS  #changed the 'bitwise or' to + operation 
    # TODO:reverse the SENSOR_STATUS variable in binary
    # to get the right one, reverse bin(198) in lopy
    msg = ustruct.pack('ffffffffffffffI', SENSOR_DATA[0],
                       SENSOR_DATA[1], SENSOR_DATA[2], SENSOR_DATA[3],
                       SENSOR_DATA[4], SENSOR_DATA[5], SENSOR_DATA[6],
                       SENSOR_DATA[7], SENSOR_DATA[8], SENSOR_DATA[9],
                       SENSOR_DATA[10], SENSOR_DATA[11], SENSOR_DATA[12],
                       SENSOR_DATA[13], SENSOR_STATUS)
    lora_sender.send(msg)
    """
    Debugging steps:
    1. check for values in scd_co2, scd_temp, scd_hum, am_temp, am_hum seperately
    2. check for values in SENSOR_DATA[0], [1], [2]...
    3. Change CONNECTION_VAR for real connection variables and not hard coded 1's f:why?
    4. Try to not round values of SENSOR_DATA f:round and *100?
    5. Try without the while loop(infinite loop)
    """