# -------------------------------------------------------------------------------
# author: Malavika Unnikrishnan, Florian Stechmann
# date: 28.09.2021
# function: Implements a normal board. Sends values every 30 secs, if threshhold
#           limits are broken every ~2 secs.
# -------------------------------------------------------------------------------

# import libraries
from machine import Pin, I2C, SoftSPI, Timer
import micropython
import ustruct
from scd30 import SCD30
from lora import LoRa
from mcp3221 import MCP3221
from bmp180 import BMP180
from am2301 import AM2301
import uheapq, time

# Allcoate emergeny buffer for interrupt signals
micropython.alloc_emergency_exception_buf(100)

# addresses of sensors
O2_ADRR = const(0x48)
CO_ADRR = const(0x49)
SCD30_ADRR = const(0x61)
AM2301_1_ADRR = const(0)
AM2301_2_ADRR = const(4)
AM2301_3_ADRR = const(17)
AM2301_4_ADRR = const(16)
SENSORBOARD_ID = const(1)
MAX_QUE = const(3)
_pkng_frmt = '>12f4H'
# Heartbeat signal
# heartbeat_msg = ustruct.pack('ffffffffffffIIII', 0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,SENSORBOARD_ID)
heartbeat_msg = ustruct.pack(_pkng_frmt, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,SENSORBOARD_ID)

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
am_temp = 0 
am_hum = 0 
que = []
error = 0
dropped_packets = []

cb_30_done = False
cb_hb_done = False

# establish I2c Bus
try:
    I2CBUS = I2C(1, sda=Pin(21), scl=Pin(22), freq=100000)
except:
    raise  # TODO:set conn_variables to sensors zero

# establish SPI Bus and LoRa (SX1276)
try:
    SPI_BUS = SoftSPI(baudrate=10000000, sck=Pin(18, Pin.OUT), mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    lora = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except:
    FAILED_LORA = 0

# create sensorobjects
try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except:
    CONNECTION_CO2 = 0
    print('Connection SCD30 failed')

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


def measure_scd30():
    """
    Takes CO2 reading.
    """
    if scd30.get_status_ready() == 1:
        return scd30.read_measurement()
    else:
        return (-1, -1, -1)


def measure_co():
    """
    Takes CO reading.
    """
    return MCP_CO.read_measurement_co()


def measure_o2():
    """
    Takes O2 reading.
    """
    return MCP_O2.read_measurement_o2()


def measure_bmp():
    """
    Takes pressure reading.
    """
    return BMP.pressure/100


def measure_am1():
    """
    Temp & humidity sensor 1 reading.
    """
    return AM2301_1.read_measurement()


def measure_am2():
    """
    Temp & humidity sensor 2 reading.
    """
    return AM2301_2.read_measurement()


def measure_am3():
    """
    Temp & humidity sensor 3 reading.
    """
    return AM2301_3.read_measurement()


def measure_am4():
    """
    Temp & humidity sensor 4 reading.
    """
    return AM2301_4.read_measurement()


def cb_30(p):
    """
    Sends the current readings from the sensors.
    """
    global cb_30_done 

    cb_30_done = True


def cb_hb(p):
    """
    Sends the heartbeat signal.
    """
    global cb_hb_done

    cb_hb_done = True


def cb_lora(p):
    """
    Callbackfunction for LoRa functionality.
    Removes a value from the queue, if an ack is received.
    """
    global que
    try:
        rcv_msg = p.decode()
        if int(rcv_msg) == SENSORBOARD_ID:
            uheapq.heappop(que)
    except Exception as e:
        print('callback lora', e)    ### catch if any error


# Thresshold limits
THRESHOLD_LIMITS = ((0.0, 1000.0), (0.0, 20.0), (19.5, 23.0), (1010.0, 1040.0),
                    (18.0, 30.0, 0.0, 100.0))

# connectionvaribles for each sensor
CONNECTION_VAR = [CONNECTION_CO2, CONNECTION_CO, CONNECTION_O2,
                  CONNECTION_BMP, CONNECTION_A1, CONNECTION_A2,
                  CONNECTION_A3, CONNECTION_A4]

# functions for taking sensor readings
FUNC_VAR = (measure_scd30, measure_co, measure_o2, measure_bmp, measure_am1,
            measure_am2, measure_am3, measure_am4)

#  Initial sleep (needed!)
time.sleep(10+SENSORBOARD_ID)

# Set callback for LoRa (recv as IR)
lora.on_recv(cb_lora)

# Create Timers
timer0 = Timer(0)
timer1 = Timer(1)

# msg init
msg = ""

# init starting timers
timer0.init(period=30000, mode=Timer.PERIODIC, callback=cb_30)
timer1.init(period=3500, mode=Timer.PERIODIC, callback=cb_hb)

#  sensor readings list init
SENSOR_DATA = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# infinite loop execution
_testing_var = 0
while True:
#     print(_testing_var)
    # print('que:', len(que), time.localtime())
    SENSOR_STATUS = 0
    LIMITS_BROKEN = 0
    j = 6

    for i in range(len(CONNECTION_VAR)):
        # Sensor Data is available & sensor is working
        func_call = FUNC_VAR[i]
        try:
            if i == 0:
                # SCD30 sensor readings (involves three values)
                reading_co2 = func_call()
                if not reading_co2[0] == -1:
                    scd_co2, scd_temp, scd_hum = reading_co2
                    if not (THRESHOLD_LIMITS[i][0] <= scd_co2 <= THRESHOLD_LIMITS[i][1]):
                        LIMITS_BROKEN = 1
                SENSOR_DATA[0] = round(scd_co2, 2) 
                SENSOR_DATA[1] = round(scd_temp, 2)
                SENSOR_DATA[2] = round(scd_hum, 2)
            elif 1 <= i <= 3:
                # MCP3221, BMP180 sensor reading
                var = func_call()
                if not (THRESHOLD_LIMITS[i][0] <= var <= THRESHOLD_LIMITS[i][1]):
                    LIMITS_BROKEN = 1
                SENSOR_DATA[i+2] = round(var, 2)  
            else:
                # AM2301 readings(involves 2 values)
                am_temp, am_hum = func_call()
                if not (THRESHOLD_LIMITS[4][0] <= am_temp <= THRESHOLD_LIMITS[4][1]):
                    LIMITS_BROKEN = 1
                if not (THRESHOLD_LIMITS[4][2] <= am_hum <= THRESHOLD_LIMITS[4][3]):
                    LIMITS_BROKEN = 1
                SENSOR_DATA[j] = am_temp 
                SENSOR_DATA[j+1] = am_hum  
                j += 2
            if CONNECTION_VAR[i] == 0:
                CONNECTION_VAR[i] = 1
        except Exception:
            CONNECTION_VAR[i] = 0

        if not CONNECTION_VAR[i]:
            # Sensor failed
            if i == 0:
                SENSOR_STATUS = 2**(i)
            elif 1 <= i <= 3:
                SENSOR_STATUS += 2**(i)
            else:
                SENSOR_STATUS += 2**(i)
    msg = ustruct.pack(_pkng_frmt, SENSOR_DATA[0], SENSOR_DATA[3],
                       SENSOR_DATA[4], SENSOR_DATA[5], SENSOR_DATA[6],
                       SENSOR_DATA[7], SENSOR_DATA[8], SENSOR_DATA[9],
                       SENSOR_DATA[10], SENSOR_DATA[11], SENSOR_DATA[12],
                       SENSOR_DATA[13], SENSOR_STATUS,
                       LIMITS_BROKEN, 0, SENSORBOARD_ID)  # current Sensorreadings

    if cb_30_done == True:
        try:
            print('len(que):', len(que))
            if que != []:
                print('{} packets dropped'.format(len(que)))
                dropped_packets += [que[0]]
                que = []
                uheapq.heappush(que, (msg, time.localtime()))
            else:
                uheapq.heappush(que, (msg, time.localtime()))
            print('msg:', ustruct.unpack(_pkng_frmt, que[0][0]), que[0][1])   ### print the latest message form tuple (msg, timestamp)
            lora.send(que[0][0])
            lora.recv()
        except Exception as e:
            print('callback 30:', e)
            error = 1
        cb_30_done = False
    
    if cb_hb_done == True:
        print('heartbeat:', ustruct.unpack(_pkng_frmt, heartbeat_msg), time.localtime())
        lora.send(heartbeat_msg)
        lora.recv()
        cb_hb_done = False
    
    if LIMITS_BROKEN:
        # print('msg:', ustruct.unpack(_pkng_frmt, msg), time.localtime())   ### print the latest message form tuple (msg, timestamp)
        lora.send(msg)  # Sends imidiately if threshold limits are broken.
        lora.recv()
    
    _testing_var += 1


