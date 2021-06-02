x-------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 19.12.2020
# function: Definert Verhalten der AM2301 Sensoren und deren Messung.
#-------------------------------------------------------------------------------

import machine, dht, time

class AM2301:
    
    def __init__(self, pin):
        """
        Setzt den Pin fest, an dem der Sensor angeschlossen ist.        
        """
	try:
	    self.pin = pin
	    self.d = dht.DHT22(machine.Pin(self.pin))
	except:
	    raise

    def read_measurement(self):
    	"""
    	Liest einmal Temperatur und rel. Luftfeuchtigkeit des AM2301 aus.
    	"""
    	try:
    	    self.d.measure()
    	    time.sleep_ms(500)
            temp = self.d.temperature()
            humid = self.d.humidity()
    	    return (temp, humid)
    	except:
    	    raise
