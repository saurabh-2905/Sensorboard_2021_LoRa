## test for ams

from machine import Pin, I2C, SoftSPI, Timer
import machine
import micropython
import ustruct, ubinascii, uhashlib
import time

from scd30 import SCD30
from lora import LoRa
from mcp3221 import MCP3221
from bmp180 import BMP180
from am2301 import AM2301

# ------------------------ function declaration -------------------------------


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


def cb_lora(p):
    """
    Callbackfunction for LoRa functionality.
    """
    try:
        msg = p.decode()
        print("Received: " + msg)
    except Exception as e:
        print("Exception occrued: " + str(e))
    global ack
    ack = True


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
    Write a given Message to the file log.txt.
    """
    with open("log", "a") as f:
        f.write(msg + "\t" + timestamp + "\n")


def add_to_que(msg, current_time):
    """
    Adds given msg to the que with a given timestamp
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
    Retuns the unique_id of the esp32
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


# Allcoate emergeny buffer for interrupt signals
micropython.alloc_emergency_exception_buf(100)

SENSORBOARD_ID = get_node_id()

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
MAX_QUEUE = const(10)
scd_co2 = 0
scd_temp = 0
scd_hum = 0
am_temp = 0
am_hum = 0

# list for measurements values
que = []

# init cb booleans
cb_30_done = False
cb_retrans_done = False

# init indicator for am reaediness
am_available1 = False
am_available2 = False
am_available3 = False
am_available4 = False
am_availability = [am_available1, am_available2, am_available3, am_available4]

# init msg intervals
msg_interval = 30000  # 30 sec
retx_interval = 5000  # 5 sec

ack = True

# ------------------------ establish connections ------------------------------
# establish I2c Bus
try:
    I2CBUS = I2C(1, sda=Pin(21), scl=Pin(22), freq=100000)
except Exception:
    # raise  # TODO:set conn_variables to sensors zero
    write_to_log('I2C failed', str(time.mktime(time.localtime())))

# establish SPI Bus and LoRa (SX1276)
try:
    SPI_BUS = SoftSPI(baudrate=10000000, sck=Pin(18, Pin.OUT),
                      mosi=Pin(23, Pin.OUT), miso=Pin(19, Pin.IN))
    lora = LoRa(SPI_BUS, True, cs=Pin(5, Pin.OUT), rx=Pin(2, Pin.IN))
except Exception:
    FAILED_LORA = 0
    write_to_log('Lora failed', str(time.mktime(time.localtime())))

# create sensorobjects
try:
    scd30 = SCD30(I2CBUS, SCD30_ADRR)
    scd30.start_continous_measurement()
except Exception:
    CONNECTION_CO2 = 0
    write_to_log('co2 failed', str(time.mktime(time.localtime())))

try:
    MCP_CO = MCP3221(I2CBUS, CO_ADRR)
except Exception:
    CONNECTION_CO = 0
    write_to_log('co failed', str(time.mktime(time.localtime())))

try:
    MCP_O2 = MCP3221(I2CBUS, O2_ADRR)
except Exception:
    CONNECTION_O2 = 0
    write_to_log('O2 failed', str(time.mktime(time.localtime())))

try:
    BMP = BMP180(I2CBUS)
except Exception:
    CONNECTION_BMP = 0
    write_to_log('pressure failed', str(time.mktime(time.localtime())))

try:
    AM2301_1 = AM2301(AM2301_1_ADRR)
except Exception:
    CONNECTION_A1 = 0
    write_to_log('AM1 failed', str(time.mktime(time.localtime())))

try:
    AM2301_2 = AM2301(AM2301_2_ADRR)
except Exception:
    CONNECTION_A2 = 0
    write_to_log('AM2 failed', str(time.mktime(time.localtime())))

try:
    AM2301_3 = AM2301(AM2301_3_ADRR)
except Exception:
    CONNECTION_A3 = 0
    write_to_log('AM3 failed', str(time.mktime(time.localtime())))

try:
    AM2301_4 = AM2301(AM2301_4_ADRR)
except Exception:
    CONNECTION_A4 = 0
    write_to_log('AM4 failed', str(time.mktime(time.localtime())))


# Thresshold limits
THRESHOLD_LIMITS = ((0.0, 1000.0), (0.0, 20.0), (18, 23.0), (950.0, 1040.0),
                    (18.0, 30.0, 0.0, 100.0))

# connectionvaribles for each sensor
CONNECTION_VAR = [CONNECTION_CO2, CONNECTION_CO,
                  CONNECTION_O2, CONNECTION_BMP,
                  CONNECTION_A1, CONNECTION_A2,
                  CONNECTION_A3, CONNECTION_A4]

SENSORS_LIST = ['CO2', 'CO', 'O2', 'BMP', 'AM1', 'AM2', 'AM3', 'AM4']

# functions for taking sensor readings
FUNC_VAR = (measure_scd30, measure_co, measure_o2, measure_bmp,
            measure_am1, measure_am2, measure_am3, measure_am4)

# Create Timers
# timer0 = Timer(0)
# timer1 = Timer(1)

# Set callback for LoRa (recv as IR)
lora.on_recv(cb_lora)

# ------------------------ infinite loop execution ----------------------------
msg = ""  # msg init

_pkg_frmt = ">8f"

print("starting loop ...")
while True:
    print("taking measurements ...")
    try:
        try:
            am1_temp, am1_hum = measure_am1()
        except Exception:
            am1_temp = 200
            am1_hum = 200

        try:
            am2_temp, am2_hum = measure_am2()
        except Exception:
            am2_temp = 200
            am2_hum = 200

        try:
            am3_temp, am3_hum = measure_am3()
        except Exception:
            am3_temp = 200
            am3_hum = 200

        try:
            am4_temp, am4_hum = measure_am4()
        except Exception:
            am4_temp = 200
            am4_hum = 200

        print("took measurements, packing msg")
        msg = ustruct.pack(_pkg_frmt, am1_temp, am1_hum,
                           am2_temp, am2_hum,
                           am3_temp, am3_hum,
                           am4_temp, am4_hum)
        msg += ustruct.pack(">L", crc32(0, msg, 32))
        ack = False
        lora.send(msg)
        lora.recv()
        print("msg sent")
    except Exception as e:
        print("Exception occured: " + str(e))
