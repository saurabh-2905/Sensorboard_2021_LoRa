# ------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 31.03.2021
# function: boot.py wird initial beim booten der MCU ausgeführt.
# 	    Stellt Verbindung mit WLAN her und legt einige wichtige Dinge fest,
# 	    wie den debug modus und den garbage collector.
# ------------------------------------------------------------------------------

import network
import esp
import gc


def no_debug():
    """
    Funktion zum festlegen des Debugverhaltens
    """
    esp.osdebug(None)


def do_connect(name="Mamba", pw="We8r21u7"):
    """
    Verbindet die MCU mit dem gegebenen WLAN-Netzwerk
    mit name = SSID und pw = password
    """
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(name, pw)
        if wlan.isconnected():
            pass


def gc_enable():
    """
    Schaltet den Garbage Collector ein.
    """
    gc.enable()


no_debug()
gc_enable()
do_connect()
