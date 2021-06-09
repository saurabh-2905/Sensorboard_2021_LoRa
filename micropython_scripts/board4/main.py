#-------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 27.04.2020
# function: main.py die nach Durchführung der boot.py ausgeführt wird.
# 	    Misst die Werte der Sensoren und bricht erst nach Abbruch durch
# 	    Eingabe oder Stromentzug ab.
#-------------------------------------------------------------------------------

from machine import Pin, I2C
from umqtt.robust import MQTTClient
import ubinascii, machine, time
from mcp3221 import MCP3221
from scd30 import SCD30
from bmp180 import BMP180
from am2301 import AM2301
import network

# Setzt die IP-Adresse des MQTT-Servers und die ID der MCU.
MQTT_SERVER = '192.168.30.17'    
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

# Setzt Konstanten für die Adressen.
O2_ADRR = 0x48
CO_ADRR = 0x49
SCD30_ADRR = 0x61
AM2301_1_ADRR = 0    
AM2301_2_ADRR = 4    
AM2301_3_ADRR = 17    
AM2301_4_ADRR = 16 

# Setzt Status der Verbindung initial auf 1 (verbunden)
FAILED_CONNECTION_O2 = 1
FAILED_CONNECTION_CO = 1
FAILED_CONNECTION_CO2 = 1
FAILED_MQTT = 1
FAILED_CONNECTION_BMP = 1
FAILED_CONNECTION_A1 = 1
FAILED_CONNECTION_A2 = 1
FAILED_CONNECTION_A3 = 1
FAILED_CONNECTION_A4 = 1
FAILED_LORA = 1

wlan = network.WLAN(network.STA_IF)
# Erstellt ein von allen Sensoren zu nutzenden I2C-Port.
try:
    I2CBUS = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
except:
    raise

# SPI Bus initialsierung
try:
    SPI_BUS = SPI(1, baudrate=10000000, sck=Pin(18, Pin.OUT), mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    SPI_BUS.init()
    lora_sender = LoRa(SPI_BUS, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except:
    FAILED_LORA = 0

# sleep um Ablauf zu gewährleisten
time.sleep(1)

# Erstellt einen Client für das Übersenden der Daten der Sensoren.
try:
   CLIENT = MQTTClient(CLIENT_ID, MQTT_SERVER)
except:
   raise

time.sleep(1)

# Objekte der einzelnen Sensoren. Für genauerer Infos siehe Klassen der Sensoren.
try:
    MCP_O2 = MCP3221(I2CBUS, O2_ADRR)
except:
    FAILED_CONNECTION_O2 = 0

try:
    MCP_CO = MCP3221(I2CBUS, CO_ADRR)
except:
    FAILED_CONNECTION_CO = 0
    
try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except:
    FAILED_CONNECTION_CO2 = 0
    
try:
    BMP = BMP180(I2CBUS)
except:
    FAILED_CONNECTION_BMP = 0
    
try:
    AM2301_1 = AM2301(AM2301_1_ADRR)
except:
    FAILED_CONNECTION_A1 = 0

try:
    AM2301_2 = AM2301(AM2301_2_ADRR)
except:
    FAILED_CONNECTION_A2 = 0

try:
    AM2301_3 = AM2301(AM2301_3_ADRR)
except:
    FAILED_CONNECTION_A3 = 0

try:
    AM2301_4 = AM2301(AM2301_4_ADRR)
except:
    FAILED_CONNECTION_A4 = 0



def send(topic, val, connect_status):
    """
    Sendet mit Hilfe des CLIENT an das übergebene :parma: topic den Wert aus :param: val,
    wenn der :param: connect_status gleich eins ist.
    """
    if connect_status == 1:
   	CLIENT.publish(topic, val)
   	
def connect_mqtt():    
    """
    Versucht eine Verbindung zu dem MQTT-Broker herzustellen.
    Wenn dies nicht gelingt, wird FAILED_MQTT auf null gesetzt.
    """
    try:
   	CLIENT.connect()
   	FAILED_MQTT = 1
    except:
    	FAILED_MQTT = 0
    	
def measure_SCD30():
    """
    Liest die Werte des SCD30 aus.    
    """
    if scd30.get_status_ready() == 1:
        return scd30.read_measurement()
    else:
        return []

#24 * 2,5s = 60s was die calibration_time ist.
def calibration_finished_test(calibration_timer):
    """
    Testet, ob die Kalibrierung abgeschlossen ist, dafür muss :param: calibration_timer
    den Wert 24 haben
    """
    if calibration_timer == 24:
    	return True
    else:
    	return False

def calibration_increment(calibration_timer):
    """
    Inkrementiert den übergebenen :param: calibration_timer um eins
    """
    return calibration_timer + 1
   
def measure_pressure():
    """
    Liest den Druck von BMP aus.    
    """
    return BMP.pressure/100
    
def measure_temperature_am_1():
    """
    Liest die Temperatur und Feuchtigkeit des AM2301 aus.    
    """
    return AM2301_1.read_measurement()


def measure_temperature_am_2():
    """
    Liest die Temperatur und Feuchtigkeit des AM2301 aus.    
    """
    return AM2301_2.read_measurement()


def measure_temperature_am_3():
    """
    Liest die Temperatur und Feuchtigkeit des AM2301 aus.    
    """
    return AM2301_3.read_measurement()


def measure_temperature_am_4():
    """
    Liest die Temperatur und Feuchtigkeit des AM2301 aus.    
    """
    return AM2301_4.read_measurement()


def do_connect(name='Mamba', pw='We8r21u7'):
    """
    Verbindet die MCU mit dem gegebenen WLAN-Netzwerk    
    mit name = SSID und pw = password
    """
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(name, pw)
        if wlan.isconnected():
            return True
    else:
        return False
        
        
# Kalibrationstimer für den O2 und den CO Sensor
calibration_timer_co = 24
calibration_timer_o2 = 24

# Verbindung zu MQTT-Broker herstellen
connect_mqtt()

# Definieren und setzen initialer Werte für die Messwerte der Sensore
# (elegantere Lösung finden!)
hum = 0
co2 = 0 
o2 = 0
co = 0
temp = 0
pressure = 0
tempa1 = 0
tempa2 = 0
tempa3 = 0
tempa4 = 0
huma1 = 0
huma2 = 0
huma3 = 0
huma4 = 0
# 60s Pause zum Kalibrieren der Sensoren
time.sleep(10)

# Und hier ein Haufen unübersichtlicher Code, welcher im wesentlichen für jeden
# Sensor versucht einen Wert auszulesen, wenn dies nicht möglich ist, weil keine
# Verbindung zu dem Sensor besteht, wird FAIL_CONNECTION_XX auf null gesetzt.
# Beim nächsten Durchlauf wird dann erneut versucht eine Verbindung zum Sensor herzustellen
# und dann ggf zu messen, ausser es muss noch kalibriert werden (O2 und CO).
# Am Ende wird geprüft, ob eine Verbindung zum MQTT-Broker besteht und ob eine WLAN
# Verbindung besteht. Wenn davon etwas nicht der Fall ist, so wird versucht die Verbiindung
# wieder herzustellen bzw. es wird gesendet wenn eine Verbindung besteht.
while True:
    if FAILED_CONNECTION_O2 == 1 and calibration_finished_test(calibration_timer_o2):
    	try:
    	    o2 = MCP_O2.read_measurement_o2()
    	except:
    	    FAILED_CONNECTION_O2 = 0
    	    calibration_timer_o2 = 0
    else:
    	try:
    	    if FAILED_CONNECTION_O2 == 0:
    	    	MCP_O2 = MCP3221(I2CBUS, O2_ADRR)
    	    	FAILED_CONNECTION_O2 = 1
    	    	calibration_timer_o2 = calibration_increment(calibration_timer_o2)
    	    else:
    	    	calibration_timer_o2 = calibration_increment(calibration_timer_o2)
    	except:
    	    FAILED_CONNECTION_O2 = 0
    	    calibration_timer_o2 = 0
    	    
    if FAILED_CONNECTION_CO == 1 and calibration_finished_test(calibration_timer_co):
    	try:
    	    co = MCP_CO.read_measurement_co()
    	    
    	except:
    	    FAILED_CONNECTION_CO = 0
    	    calibration_timer_co = 0
    else:
    	try:
    	    if FAILED_CONNECTION_CO == 0:
    	    	MCP_CO = MCP3221(I2CBUS, CO_ADRR)
    	    	FAILED_CONNECTION_CO = 1
    	    	calibration_timer_co = calibration_increment(calibration_timer_co)
    	    else:
    	    	calibration_timer_co = calibration_increment(calibration_timer_co)
    	except:
    	    FAILED_CONNECTION_CO = 0
    	    calibration_timer_co = 0
 
    if FAILED_CONNECTION_CO2 == 1:
    	try:
            measurement_scd30 = measure_SCD30()
            if not measurement_scd30 == []:
    	    	co2 = measurement_scd30[0]
    	    	hum = measurement_scd30[1]
    	    	temp = measurement_scd30[2]
    	except:
    	    FAILED_CONNECTION_CO2 = 0
    else:
    	try:
    	    FAILED_CONNECTION_CO2 = 1
    	    measurement_scd30 = measure_SCD30()
    	    if not measurement_scd30 == []:
    	    	co2 = measurement_scd30[0]
    	    	hum = measurement_scd30[1]
    	    	temp = measurement_scd30[2]
	except:
      	    FAILED_CONNECTION_CO2 = 0
      	    
    if FAILED_CONNECTION_BMP == 1:
    	try:
            pressure = measure_pressure()
    	except:
    	    FAILED_CONNECTION_BMP = 0
    else:
    	try:
    	    BMP = BMP180(I2CBUS)
    	    pressure = measure_pressure()
    	    FAILED_CONNECTION_BMP = 1
	except:
      	    FAILED_CONNECTION_BMP = 0
      	    
    if FAILED_CONNECTION_A1 == 1:
    	try:
    	    res = measure_temperature_am_1()	
    	    if not res == []:
            	tempa1 = res[0]
            	huma1 = res[1]
    	except:
    	    FAILED_CONNECTION_A1 = 0
    else:
    	try:
    	    AM2301_1 = AM2301(AM2301_1_ADRR)
    	    time.sleep_ms(2000)
    	    res = measure_temperature_am_1()	
    	    if not res == []:
            	tempa1 = res[0]
            	huma1 = res[1]
    	    FAILED_CONNECTION_A1 = 1
	except:
      	    FAILED_CONNECTION_A1 = 0
      	    
    if FAILED_CONNECTION_A2 == 1:
    	try:
    	    res2 = measure_temperature_am_2()
    	    if not res2 == []:	
            	tempa2 = res2[0]
            	huma2 = res2[1]
    	except:
    	    FAILED_CONNECTION_A2 = 0
    else:
    	try:
    	    AM2301_2 = AM2301(AM2301_2_ADRR)
    	    time.sleep_ms(2000)
    	    res2 = measure_temperature_am_2()
    	    if not res2 == []:	
            	tempa2 = res2[0]
            	huma2 = res2[1]
    	    FAILED_CONNECTION_A2 = 1
	except:
      	    FAILED_CONNECTION_A2 = 0
    
    if FAILED_CONNECTION_A3 == 1:
    	try:
    	    res3 = measure_temperature_am_3()
    	    if not res3 == []:	
            	tempa3 = res3[0]
            	huma3 = res3[1]
    	except:
    	    FAILED_CONNECTION_A3 = 0
    else:
    	try:
    	    AM2301_3 = AM2301(AM2301_3_ADRR)
    	    time.sleep_ms(2000)
    	    res3 = measure_temperature_am_3()
    	    if not res3 == []:	
            	tempa3 = res3[0]
            	huma3 = res3[1]
    	    FAILED_CONNECTION_A3 = 1
	except:
      	    FAILED_CONNECTION_A3 = 0
    
    if FAILED_CONNECTION_A4 == 1:
    	try:
    	    res4 = measure_temperature_am_4()
    	    if not res4 == []:	
            	tempa4 = res4[0]
            	huma4 = res4[1]
    	except:
    	    FAILED_CONNECTION_A4 = 0
    else:
    	try:
    	    AM2301_4 = AM2301(AM2301_4_ADRR)
    	    time.sleep_ms(2000)
    	    res4 = measure_temperature_am_4()
    	    if not res4 == []:	
            	tempa4 = res4[0]
            	huma4 = res4[1]
    	    FAILED_CONNECTION_A4 = 1
	except:
      	    FAILED_CONNECTION_A4 = 0
    
    if wlan.isconnected() and FAILED_MQTT == 1:
    	send('board4/co2_scd', str(co2), FAILED_CONNECTION_CO2)
    	send('board4/humid_scd', str(hum), FAILED_CONNECTION_CO2)
    	send('board4/temp_scd', str(temp), FAILED_CONNECTION_CO2)
    	send('board4/co', str(co), FAILED_CONNECTION_CO)
    	send('board4/o2', str(o2), FAILED_CONNECTION_O2)
    	send('board4/amb_press', str(pressure), FAILED_CONNECTION_BMP)
    	send('board4/temp1_am', str(tempa1), FAILED_CONNECTION_A1)
    	send('board4/humid1_am', str(huma1), FAILED_CONNECTION_A1)
    	send('board4/temp2_am', str(tempa2), FAILED_CONNECTION_A2)
    	send('board4/humid2_am', str(huma2), FAILED_CONNECTION_A2)
    	send('board4/temp3_am', str(tempa3), FAILED_CONNECTION_A3)
    	send('board4/humid3_am', str(huma3), FAILED_CONNECTION_A3)
    	send('board4/temp4_am', str(tempa4), FAILED_CONNECTION_A4)
    	send('board4/humid4_am', str(huma4), FAILED_CONNECTION_A4)
    else:
        do_connect()
        connect_mqtt()

#random comment
