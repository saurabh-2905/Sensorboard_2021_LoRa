# -------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 19.04.2022
# function: realizes bmp180 from bosch functionality via I2C bus.
# -------------------------------------------------------------------------------

from machine import I2C

import ustruct


class BMP180():
    """
    """

    _BMP_ADRESS = 119

    def __init__(self, i2cbus, os=3):
        """
        """
        self.i2cbus = i2cbus
        if os > 3 or os < 0:
            self.oversample_setting = 3
        else:
            self.oversample_setting = os

        if not self._BMP_ADRESS in self.i2cbus.scan():
            raise

    def get_data(self):
        """
        """
        self._get_measurement_data()
        pressure = self._calculate_pressure()
        temperature = self._calculate_temperature()
        return (pressure, temperature)

    def set_oversample_setting(self, os):
        """
        """
        if os > 3 or os < 0:
            self.oversample_setting = 3
        else:
            self.oversample_setting = os

    def _get_measurement_data(self):
        """
        """
        return True

    def _calculate_pressure(self):
        """
        """
        return True

    def _calculate_temperature(self):
        """
        """
        return True
