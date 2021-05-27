#-------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 31.03.2020
# function: main.py die nach Durchführung der boot.py ausgeführt wird.
# 	    Misst die Werte der Sensoren und bricht erst nach Abbruch durch
# 	    Eingabe oder Stromentzg ab.
#-------------------------------------------------------------------------------

from machine import Pin, I2C
import ubinascii, machine, time

from mcp3221 import MCP3221
from scd30 import SCD30
from bmp180 import BMP180
from am2301 import AM2301

# Setzt die IP-Adresse des MQTT-Servers und die ID der MCU, sowie das WLAN objekt.
WLAN = network.WLAN(network.STA_IF)
MQTT_SERVER = "192.168.30.17"    
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

# Setzt Konstanten für die Adressen.
O2_ADRR = const(0x48)
CO_ADRR = const(0x49)
SCD30_ADRR = const(0x61)
AM2301_1_ADRR = const(0)
AM2301_2_ADRR = const(4)
AM2301_3_ADRR = const(17)  
AM2301_4_ADRR = const(16)

# Setzt Status der Verbindung initial auf 1 (verbunden)
CONNECTION_O2 = 1
CONNECTION_CO = 1
CONNECTION_CO2 = 1
CONNECTION_BMP = 1
CONNECTION_AM1 = 1
CONNECTION_AM2 = 1
CONNECTION_AM3 = 1
CONNECTION_AM4 = 1
CONNECTION_LORA = 1

# Erstellt ein von allen Sensoren zu nutzenden I2C-Port.
try:
    I2CBUS = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
except:
    raise

# SPI Bus initialsierung
try:
    SPI_BUS = SPI(1, baudrate=10000000, sck=Pin(18, Pin.OUT), mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    SPI_BUS.init()
    lora_sender = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except:
    FAILED_LORA = 0

# Objekte der einzelnen Sensoren. Für genauerer Infos siehe Klassen der Sensoren.
try:
    mcp_o2 = MCP3221(I2CBUS, O2_ADRR)
except:
    CONNECTION_O2 = 0

try:
    mcp_co = MCP3221(I2CBUS, CO_ADRR)
except:
    CONNECTION_CO = 0
    
try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except:
    CONNECTION_CO2 = 0
    
try:
    bmp180 = BMP180(I2CBUS)
except:
    CONNECTION_BMP = 0
    
try:
    am2301_1 = AM2301(AM2301_1_ADRR)
except:
    CONNECTION_AM1 = 0

try:
    am2301_2 = AM2301(AM2301_2_ADRR)
except:
    CONNECTION_AM2 = 0

try:
    am2301_3 = AM2301(AM2301_3_ADRR)
except:
    CONNECTION_AM3 = 0

try:
    am2301_4 = AM2301(AM2301_4_ADRR)
except:
    CONNECTION_AM4 = 0
    	
def measure_SCD30():
    """
    Liest die Werte des SCD30 aus.    
    """
    if scd30.get_status_ready() == 1:
        return scd30.read_measurement()
    else:
        return ("F", "F", "F")
   
def measure_amb_press():
    """
    Liest den Druck von BMP aus.    
    """
    return bmp180.pressure/100

def measure_o2():
    """
    """
    return mcp_o2.read_measurement_o2()

def measure_co():
    """
    """
    return mcp_co.read_measurement_co()

def measure_am1():
    """
    """
    return am2301_1.read_measurement()

def measure_am2():
    """
    """
    return am2301_2.read_measurement()

def measure_am3():
    """
    """
    return am2301_3.read_measurement()

def measure_am4():
    """
    """
    return am2301_4.read_measurement()

def measure_and_check(conn_stat, meas_func, number):
    """
    """
    if conn_stat == 1:
        try:
            # TODO: SPEICHERALLOKATION OPTIMIEREN!
            return meas_func()
        except:
            conn_stat = 0
            return "F"+str(number)
    else:
        try:
            # TODO: SPEICHERALLOKATION OPTIMIEREN!
            ret = measu_func()
            conn_stat = 1
            return ret
        except:
            conn_stat = 0
            return "F"

# time for calibration
time.sleep(10)

# Endless loop
while True:

    
