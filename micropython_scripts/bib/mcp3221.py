#-------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 01.04.2021
# function: Definiert das Verhalten der MCP3221 Sensoren zum Messen und
# 	    Mitteln der gemessenen Werte.
#-------------------------------------------------------------------------------

from machine import I2C
import time

class MCP3221:
    """
    Treiber für die Sensoren auf den MCP3221.
    """
    #Setzt Konstanten, die zum Auslesen und Berechnen der Daten benötigt werden.
    BYTES_TO_READ = 2
    COEFFICIENT_O2 = 20.9/1712
    COEFFICIENT_CO = 1000/2440

    def __init__(self, i2cbus, address):
	"""
	Initialisiert das von dieser Klasse erstellte Objekt und schmeißt eine Exception, 
	falls die übergebene Adresse nicht an den MCU angeschlossen ist.
	"""
        self.i2c = i2cbus
        self.addr = address
        if not self.addr in self.i2c.scan():
            raise

    def read_measurement_o2(self):
	"""
	Liest die Daten des O2-Sensors aus und gibt diese zurück.
	"""
	input_data = self.i2c.readfrom(self.addr, self.BYTES_TO_READ)
	raw_data = input_data[0] << 8 | input_data[1]
	
        return raw_data*self.COEFFICIENT_O2

    def read_measurement_co(self):
	"""
	Liest die Daten des CO-Sensors aus und gibt diese zurück.
	"""
	input_data = self.i2c.readfrom(self.addr, self.BYTES_TO_READ)
	raw_data = input_data[0] << 8 | input_data[1]
	
	if raw_data < 17:
            return 0
        else:
            return (raw_data-17)*self.COEFFICIENT_CO


	
	
