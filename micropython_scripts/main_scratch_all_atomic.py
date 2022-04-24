# -------------------------------------------------------------------------------
# author: Malavika Unnikrishnan, Florian Stechmann, Saurabh Band
# date: 24.04.2022
# function: Code for esp32 board with lora module.
# -------------------------------------------------------------------------------

from machine import Pin, I2C, SoftSPI, Timer
import machine
import micropython
import ustruct, ubinascii, uhashlib
import time
import random

from scd30 import SCD30
from lora import LoRa
from mcp3221 import MCP3221
from bmp180 import BMP180
from am2301 import AM2301

# ------------------------ function declaration -------------------------------


def measure_scd30(stat):
    """
    Takes CO2 reading.
    """
    try:
        if scd30.get_status_ready() == 1:
            SENSOR_VALUES[0] = scd30.read_measurement()[0]
            CONNECTION_VAR[stat] = 1
        else:
            SENSOR_VALUES[0] = -1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_co(stat):
    """
    Takes CO reading.
    """
    try:
        SENSOR_VALUES[1] = MCP_CO.read_measurement_co()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_o2(stat):
    """
    Takes O2 reading.
    """
    try:
        SENSOR_VALUES[2] = MCP_O2.read_measurement_o2()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_bmp(stat):
    """
    Takes pressure reading.
    """
    try:
        SENSOR_VALUES[3] = BMP.pressure
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_am1(stat):
    """
    Temp & humidity sensor 1 reading.
    """
    global am_temp, am_hum
    try:
        am_temp, am_hum = AM2301_1.read_measurement()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_am2(stat):
    """
    Temp & humidity sensor 2 reading.
    """
    global am_temp, am_hum
    try:
        am_temp, am_hum = AM2301_2.read_measurement()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_am3(stat):
    """
    Temp & humidity sensor 3 reading.
    """
    global am_temp, am_hum
    try:
        am_temp, am_hum = AM2301_3.read_measurement()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def measure_am4(stat):
    """
    Temp & humidity sensor 4 reading.
    """
    global am_temp, am_hum
    try:
        am_temp, am_hum = AM2301_4.read_measurement()
        CONNECTION_VAR[stat] = 1
    except Exception:
        CONNECTION_VAR[stat] = 0


def cb_30(p):
    """
    Callback for the sending of msgs every btw 20s-40s.
    """
    global cb_30_done
    cb_30_done = True


def cb_retrans(p):
    """
    Callback for resending msgs.
    """
    global cb_retrans_done
    cb_retrans_done = True


def lora_scheduled(r_msg):
    """
    Scheduled lora callback.
    """
    global cb_lora_recv, rcv_msg
    cb_lora_recv = True
    rcv_msg.append(r_msg)


def cb_lora(p):
    """
    Schedules lora callback.
    """
    micropython.schedule(lora_scheduled, p)


def crc32(crc, p, len):
    """
    crc = 0
    p = message
    len = length of msg
    """
    crc = 0xffffffff & ~crc
    for i in range(len):
        crc = crc ^ p[i]
        for j in range(8):
            crc = (crc >> 1) ^ (0xedb88320 & -(crc & 1))
    return 0xffffffff & ~crc


def write_to_log(msg, timestamp):
    """
    Write a given message to the file log.txt.
    """
    with open("log", "a") as f:
        f.write(msg + "\t" + timestamp + "\n")


def add_to_que(msg, current_time):
    """
    Adds given msg to the que with a given timestamp.
    """
    global que
    if len(que) >= MAX_QUEUE:
        # pop the packet from the end of que (the oldest packet)
        que.pop()
        # add the newest msg at the front of que
        que = [(msg, current_time)] + que
    else:
        que = [(msg, current_time)] + que


def get_nodename():
    """
    Retuns the unique_id of the esp32.
    """
    uuid = ubinascii.hexlify(machine.unique_id()).decode()
    node_name = "ESP_" + uuid
    return node_name


def get_node_id(hex=False):
    """
    Get node id, which consists of four bytes unsigned int.
    Return as hex, according to parameter.
    """
    node_id = ubinascii.hexlify(uhashlib.sha1(
        machine.unique_id()).digest()).decode("utf-8")[-8:]
    if hex:
        return node_id
    else:
        return int(node_id, 16)


def lora_rcv_exec(p):
    """
    Processes all received lora msgs.
    """
    global cb_lora_recv, rcv_msg
    if cb_lora_recv:
        cb_lora_recv = False
        for i in range(len(rcv_msg)):
            msg = rcv_msg[i]
            try:
                recv_msg = msg.decode()
                board_id, timestamp = recv_msg.split(",")
                if int(board_id) == SENSORBOARD_ID:
                    for each_pkt in que:
                        if each_pkt[1] == int(timestamp):
                            que.remove(each_pkt)
            except Exception:
                pass
        rcv_msg = []


# ------------------------ constants and variables ----------------------------
# addresses of sensors
O2_ADRR = const(0x48)
CO_ADRR = const(0x49)
SCD30_ADRR = const(0x61)
AM2301_1_ADRR = const(0)
AM2301_2_ADRR = const(4)
AM2301_3_ADRR = const(17)
AM2301_4_ADRR = const(16)

# connection_variables init for sensors
FAILED_LORA = 1
CONNECTION_CO2 = 1
CONNECTION_CO = 1
CONNECTION_O2 = 1
CONNECTION_BMP = 1
CONNECTION_A1 = 1
CONNECTION_A2 = 1
CONNECTION_A3 = 1
CONNECTION_A4 = 1

# maximum number of values in queue
MAX_QUEUE = const(10)

# initial values for sensors
scd_co2 = 0
mcp_co = 0
mcp_o2 = 0
bmp_pres = 0
am_temp = 0
am_hum = 0


# list for measurements values
que = []

# init cb booleans
cb_30_done = False
cb_retrans_done = False
cb_lora_recv = False

# initial msg intervals
msg_interval = 30000  # 30 sec
retx_interval = 5000  # 5 sec

# packing format
_pkng_frmt = ">12f3HI"
SENSORBOARD_ID = get_node_id()

# allcoate emergeny buffer for interrupt signals
micropython.alloc_emergency_exception_buf(100)

# ------------------------ establish connections ------------------------------
# establish I2c Bus
try:
    I2CBUS = I2C(1, sda=Pin(21), scl=Pin(22), freq=100000)
except Exception:
    # raise  # TODO:set conn_variables to sensors zero
    write_to_log("I2C failed", str(time.mktime(time.localtime())))

# establish SPI Bus and LoRa (SX1276)
try:
    SPI_BUS = SoftSPI(baudrate=10000000, sck=Pin(18, Pin.OUT),
                      mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    lora = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except Exception:
    FAILED_LORA = 0
    write_to_log("Lora failed", str(time.mktime(time.localtime())))

# create sensorobjects
try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except Exception:
    CONNECTION_CO2 = 0
    write_to_log("co2 failed", str(time.mktime(time.localtime())))

try:
    MCP_CO = MCP3221(I2CBUS, CO_ADRR)
except Exception:
    CONNECTION_CO = 0
    write_to_log("co failed", str(time.mktime(time.localtime())))

try:
    MCP_O2 = MCP3221(I2CBUS, O2_ADRR)
except Exception:
    CONNECTION_O2 = 0
    write_to_log("O2 failed", str(time.mktime(time.localtime())))

try:
    BMP = BMP180(I2CBUS)
except Exception:
    CONNECTION_BMP = 0
    write_to_log("pressure failed", str(time.mktime(time.localtime())))

try:
    AM2301_1 = AM2301(AM2301_1_ADRR)
except Exception:
    CONNECTION_A1 = 0
    write_to_log("AM1 failed", str(time.mktime(time.localtime())))

try:
    AM2301_2 = AM2301(AM2301_2_ADRR)
except Exception:
    CONNECTION_A2 = 0
    write_to_log("AM2 failed", str(time.mktime(time.localtime())))

try:
    AM2301_3 = AM2301(AM2301_3_ADRR)
except Exception:
    CONNECTION_A3 = 0
    write_to_log("AM3 failed", str(time.mktime(time.localtime())))

try:
    AM2301_4 = AM2301(AM2301_4_ADRR)
except Exception:
    CONNECTION_A4 = 0
    write_to_log("AM4 failed", str(time.mktime(time.localtime())))


# thresshold limits
THRESHOLD_LIMITS = ((0.0, 3000.0), (0.0, 20.0), (18, 23.0), (950.0, 1040.0),
                    (18.0, 30.0, 0.0, 100.0))

# connectionvaribles for each sensor
CONNECTION_VAR = [CONNECTION_CO2, CONNECTION_CO,
                  CONNECTION_O2, CONNECTION_BMP,
                  CONNECTION_A1, CONNECTION_A2,
                  CONNECTION_A3, CONNECTION_A4]

# list with all sensor names for log purposes
SENSORS_LIST = ("CO2", "CO", "O2", "BMP", "AM1", "AM2", "AM3", "AM4")

# values from measure functions,
# except for AMs (they are taken care of elsewhere)
SENSOR_VALUES = [scd_co2, mcp_co, mcp_o2, bmp_pres]

# functions for taking sensor readings
FUNC_VAR = (measure_scd30, measure_co, measure_o2, measure_bmp,
            measure_am1, measure_am2, measure_am3, measure_am4)

# create Timers
timer0 = Timer(0)
timer1 = Timer(1)

# set callback for LoRa (recv as IR)
lora.on_recv(cb_lora)

# sensor readings list init
SENSOR_DATA = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# ------------------------ infinite loop execution ----------------------------
msg = ""  # msg init
rcv_msg = []  # rcv_msg init

# initialize timer
# Timer for sending msgs with measurement values + timestamp + crc
timer0.init(period=msg_interval, mode=Timer.ONE_SHOT, callback=cb_30)

# get the start time of the script in seconds wrt the localtime
start_time = time.mktime(time.localtime())
retransmit_count = 0

while True:
    # get the current time of the script in seconds wrt the localtime
    current_time = time.mktime(time.localtime())
    SENSOR_STATUS = 0
    LIMITS_BROKEN = 0
    j = 6

    for i in range(len(CONNECTION_VAR)):
        # take readings for all sensors, also note if one is not working
        func_call = FUNC_VAR[i]
        try:
            if i < 4:
                # readings for CO2, CO, O2 and pressure are taken.
                micropython.schedule(func_call, i)
                val = SENSOR_VALUES[i]
                if not val == -1:
                    if not (THRESHOLD_LIMITS[i][0] <= val <= THRESHOLD_LIMITS[i][1]):
                        LIMITS_BROKEN = 1
                SENSOR_DATA[i] = round(val, 2)
            else:
                # AM2301 readings (involves 2 values)
                micropython.schedule(func_call, i)
                if not (THRESHOLD_LIMITS[4][0] <= am_temp <= THRESHOLD_LIMITS[4][1]):
                    LIMITS_BROKEN = 1
                if not (THRESHOLD_LIMITS[4][2] <= am_hum <= THRESHOLD_LIMITS[4][3]):
                    LIMITS_BROKEN = 1
                SENSOR_DATA[j] = am_temp
                SENSOR_DATA[j+1] = am_hum
                j += 2
        except Exception as e:
            CONNECTION_VAR[i] = 0
            write_to_log("failed {}: {}".format(SENSORS_LIST[i], e),
                         str(current_time))

        if not CONNECTION_VAR[i]:
            # sensor failed
            if i < 4:
                SENSOR_STATUS += 2**(i)
            else:
                SENSOR_STATUS += 2**(i)

    # prepare the packted to be sent
    msg = ustruct.pack(_pkng_frmt, SENSOR_DATA[0], SENSOR_DATA[1],
                       SENSOR_DATA[2], SENSOR_DATA[3], SENSOR_DATA[4],
                       SENSOR_DATA[5], SENSOR_DATA[6], SENSOR_DATA[7],
                       SENSOR_DATA[8], SENSOR_DATA[9], SENSOR_DATA[10],
                       SENSOR_DATA[11], SENSOR_STATUS, LIMITS_BROKEN,
                       0, SENSORBOARD_ID)  # current Sensorreadings
    msg += ustruct.pack(">L", current_time)  # add timestamp to the msg
    msg += ustruct.pack(">L", crc32(0, msg, 62))  # add 32-bit crc to the msg

    micropython.schedule(lora_rcv_exec, 0)  # process received msgs

    if LIMITS_BROKEN:
        add_to_que(msg, current_time)
        lora.send(msg)  # Sends imidiately if threshold limits are broken.
        lora.recv()
    elif cb_30_done:  # send the messages every 30 seconds
        try:
            add_to_que(msg, current_time)
            lora.send(que[0][0])
            lora.recv()
        except Exception as e:
            write_to_log("callback 30: {}".format(e), str(current_time))
        start_time = current_time
        timer1.init(period=retx_interval, mode=Timer.PERIODIC, callback=cb_retrans)
        timer0.init(period=msg_interval, mode=Timer.ONE_SHOT, callback=cb_30)

        # randomize the msg interval to avoid continous collision of packets
        if random.random() >= 0.4:
            # select time randomly with steps of 1000ms, because the max on
            # air time is 123ms and 390ms for SF7 and SF9 resp.
            msg_interval = random.randrange(20000, 40000, 1000)
            # select random time interval with step size of 1 sec
            retx_interval = random.randrange(2000, 10000, 1000)

        # reset timer boolean
        cb_30_done = False
    elif cb_retrans_done:  # retransmit every 5 seconds for pkts with no ack
        cb_retrans_done = False
        retransmit_count += 1
        if que != []:
            lora.send(que[0][0])
            lora.recv()
        if retransmit_count >= 2:
            timer1.deinit()
            retransmit_count = 0
