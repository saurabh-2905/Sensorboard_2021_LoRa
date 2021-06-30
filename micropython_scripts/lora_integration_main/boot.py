# ------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 31.03.2021
# function: boot.py wird initial beim booten der MCU ausgeführt.
# 	    Stellt Verbindung mit WLAN her und legt einige wichtige Dinge fest,
# 	    wie den debug modus und den garbage collector.
# ------------------------------------------------------------------------------

import esp
import gc


def no_debug():
    """
    Funktion zum festlegen des Debugverhaltens
    """
    esp.osdebug(None)


def gc_enable():
    """
    Schaltet den Garbage Collector ein.
    """
    gc.enable()


no_debug()
gc_enable()
