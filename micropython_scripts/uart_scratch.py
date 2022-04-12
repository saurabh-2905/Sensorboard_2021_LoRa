# For testing URAT on Sparkfun ESP32 Thing

from machine import UART

msg = ''  # message to be send via UART


# SparkFun ESP32 Thing UART PinOut for rx and tx Pin
#     UART0  UART1   UART2
# tx  1      10      17
# rx  3       9      16
uart1 = UART(1, baudrate=9600, tx=17, rx=16)
uart1.write(msg)  # write no of byte to TX pin specified in uart1 object
## scetch works
