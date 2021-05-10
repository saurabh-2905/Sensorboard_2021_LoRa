#-------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 31.03.2021
# function: boot.py wird initial beim booten der MCU ausgeführt.
# 	    Stellt Verbindung mit WLAN her und legt einige wichtige Dinge fest,
# 	    wie den debug modus und den garbage collector.
#-------------------------------------------------------------------------------

def no_debug():
    """
    Funktion zum festlegen des Debugverhaltens
    """
    import esp
    esp.osdebug(None)

def do_connect(name, pw):
    """
    Verbindet die MCU mit dem gegebenen WLAN-Netzwerk    
    mit name = SSID und pw = password
    """
    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(name, pw)
        if wlan.isconnected():
            pass
        
def gc_enable():
    import gc
    gc.enable()

# Schaltet die LED aus und verbindet mit dem WLAN und no_debug und gc wird eingeschaltet.
no_debug()
gc_enable()
do_connect('Mamba', 'We8r21u7')

