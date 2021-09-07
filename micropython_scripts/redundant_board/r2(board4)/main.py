# -------------------------------------------------------------------------------
# author: Malavika Unnikrishnan, Florian Stechmann
# date: 07.09.2021
# function: Implements a redundant board. Sends values every 4 min, if board 1
#           fails sends every 30 secs. Send every ~2 secs if threshold limits
#           are broken (see below).
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
SENSORBOARD_ID = const(4)
REDUNDANT_HEARTBEAT = const(1)

# Heartbeat signal
heartbeat_msg = ustruct.pack('I', SENSORBOARD_ID)

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

counter_redundancy = 0

EMERGENCY_STATUS = 0

# establish I2c Bus
try:
    I2CBUS = I2C(1, sda=Pin(21), scl=Pin(22), freq=100000)
except:
    raise

# establish SPI Bus and LoRa (SX1276)
try:
    SPI_BUS = SoftSPI(baudrate=10000000, sck=Pin(18, Pin.OUT), mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    lora = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except:
    FAILED_LORA = 0
    
# creating Sensorobjects
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
    uheapq.heappush(que, msg)
    lora.send(que[0])
    lora.recv()


def cb_hb(p):
    """
    Sends the heartbeat signal.
    """
    lora.send(heartbeat_msg)
    lora.recv()


def cb_lora(p):
    """
    Callbackfunction for LoRa functionality.
    Removes a value from the queue, if an ack is received.
    Also receives the redundant heartbeat signal.
    """
    global counter_redundancy
    try:
        rcv_msg = int(p.decode())
        if rcv_msg == SENSORBOARD_ID:
            uheapq.heappop(que)
    except Exception:
        rcv_msg = ustruct.unpack('I', p)[0]
        if rcv_msg == REDUNDANT_HEARTBEAT:
            counter_redundancy = 0
            emergency_mode(0)


def cb_r(p):
    """
    Callbackfunction for the redundancy.
    Increments counter, if the counter is bigger than 1,
    sets itself to emergency mode.
    """
    global counter_redundancy
    counter_redundancy += 1
    if counter_redundancy == 2:
        emergency_mode(1)


def emergency_mode(mode):
    """
    Can set the emergency mode: :param: equals 1, or
    remove the emergency mode: :param: equals 0.
    """
    global EMERGENCY_STATUS
    if mode:
        EMERGENCY_STATUS = 1
        timer0.deinit()
        timer2.init(period=30000, mode=Timer.PERIODIC, callback=cb_30)
    elif mode == 0 and EMERGENCY_STATUS:
        timer2.deinit()
        timer0.init(period=240000, mode=Timer.PERIODIC, callback=cb_30)
        EMERGENCY_STATUS = 0

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
timer2 = Timer(2)
timer3 = Timer(3)

# msg init
msg = ""

# init starting timers
timer3.init(period=4500, mode=Timer.PERIODIC, callback=cb_r)
timer1.init(period=3500, mode=Timer.PERIODIC, callback=cb_hb)
timer0.init(period=240000, mode=Timer.PERIODIC, callback=cb_30)  

# sensor readings list init
SENSOR_DATA = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# infinite loop execution
while True:
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
                SENSOR_DATA[0] = round(scd_co2, 2)r
                SENSOR_DATA[1] = round(scd_temp, 2)
                SENSOR_DATA[2] = round(scd_hum, 2)
            elif 1 <= i <= 3:
                # MCP3221, BMP180 sensor reading
                var = func_call()
                if not (THRESHOLD_LIMITS[i][0] <= var <= THRESHOLD_LIMITS[i][1]):
                    LIMITS_BROKEN = 1
                SENSOR_DATA[i+2] = round(var, 2)r
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
    msg = ustruct.pack('ffffffffffffIIII', SENSOR_DATA[0], SENSOR_DATA[3],
                       SENSOR_DATA[4], SENSOR_DATA[5], SENSOR_DATA[6],
                       SENSOR_DATA[7], SENSOR_DATA[8], SENSOR_DATA[9],
                       SENSOR_DATA[10], SENSOR_DATA[11], SENSOR_DATA[12],
                       SENSOR_DATA[13], SENSOR_STATUS,
                       LIMITS_BROKEN, 0, SENSORBOARD_ID)  # current Sensorreadings
    
    if LIMITS_BROKEN:
        lora.send(msg)  # Sends imidiately if threshold limits are broken.
        lora.recv()
