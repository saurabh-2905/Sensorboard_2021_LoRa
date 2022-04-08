# ------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 08.04.2022
# function: Definert Verhalten der AM2301 Sensoren und deren Messung.
# ------------------------------------------------------------------------------

import machine
import dht
import time


class AM2301:
    """
    Definiert AM2301 Ansprechverhalten.
    """
    def __init__(self, pin):
        """
        Setzt den Pin fest, an dem der Sensor angeschlossen ist.
        """
        try:
            self.pin = pin
            self.d = dht.DHT22(machine.Pin(self.pin))
        except Exception:
            raise

    def read_measurement(self):
        """
        Liest einmal Temperatur und rel. Luftfeuchtigkeit des AM2301 aus.
        """
        for i in range(3):
            try:
                self.d.measure()
                time.sleep_ms(500)
                temp = self.d.temperature()
                humid = self.d.humidity()
                return (temp, humid)
            except Exception:
                if i == 2:
                    raise
                else:
                    pass
