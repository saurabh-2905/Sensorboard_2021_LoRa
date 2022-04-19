# -------------------------------------------------------------------------------
# author: Florian Stechmann
# date: 19.04.2022
# function: realizes bmp180 from bosch functionality via I2C bus.
# -------------------------------------------------------------------------------

from machine import I2C

import ustruct
import time


class BMP180():
    """
    """

    _BMP_ADRESS = 119

    # Calibration registers
    AC1 = 0
    AC2 = 0
    AC3 = 0
    AC4 = 0
    AC5 = 0
    AC6 = 0
    B1 = 0
    B2 = 0
    MB = 0
    MC = 0
    MD = 0

    # CMD registers
    CMD_REG = bytearray([0xF4])
    MSB_REG = bytearray([0xF6])
    LSB_REG = bytearray([0xF7])
    XLSB_REG = bytearray([0xF8])

    # Raw temperature value
    UT_raw = 0

    # Raw pressure value
    UP_raw = 0

    def __init__(self, i2cbus, os=3):
        """
        Constructor for initilization.
        """
        self.i2cbus = i2cbus

        # Checks whether the sensor with the given address is available.
        if not self._BMP_ADRESS in self.i2cbus.scan():
            raise

        if os > 3 or os < 0:
            self.oversampling_setting = 3
        else:
            self.oversampling_setting = os

        self._get_calib_coefficents()

    def get_temp_pres(self):
        """
        Returns temperature and pressure readings of the sensor.
        """
        try:
            self._get_measurement_data()
            temperature, B5 = self._calculate_temperature()
            pressure = self._calculate_pressure(B5)
            return (pressure, temperature)
        except Exception:
            raise

    def set_oversampling_setting(self, os):
        """
        Changes the oversampling_setting os, which determines the
        precision of the measurements, and by that the time it takes
        to obtain a sample. Valid Values are 0 to 3:
        0: 1 internal sample, 4.5 s max.
        1: 2 internal sample, 7.5 s max.
        2: 3 internal sample, 13.5 s max.
        3: 4 internal sample, 25.5 s max.
        """
        if os > 3 or os < 0:
            self.oversampling_setting = 3
        else:
            self.oversampling_setting = os

    def _get_measurement_data(self):
        """
        Requests measurement data and stores raw measurement values in
        UT and UP.
        """
        pressure_cmd = 0x34 + (self.oversampling_setting << 6)
        PRES_MEAS_CMD = bytearray([pressure_cmd])
        TEMP_MEAS_CMD = bytearray([0x2E])
        try:
            self.i2cbus.writeto_mem(self._BMP_ADRESS,
                                    self.CMD_REG, TEMP_MEAS_CMD, 2)
            time.sleep_ms(4.5)
            self.UT_raw = self.i2cbus.readfrom_mem(self._BMP_ADRESS,
                                                   self.MSB_REG, 2)
            self.i2cbus.writeto_mem(self._BMP_ADRESS,
                                    self.CMD_REG, PRES_MEAS_CMD, 2)
            self.UP_raw = self.i2cbus.readfrom_mem(self._BMP_ADRESS,
                                                   self.MSB_REG, 3)
        except Exception:
            raise

    def _calculate_temperature(self):
        """
        Calculates temperature in grad celsius.
        """
        try:
            UT = self.UT_raw[0] << 8 + self.UT_raw[1]
        except Exception:
            raise
        X1 = (UT-self.AC6)*self.AC5/2**15
        X2 = self.MC*2**11/(X1+self.MD)
        B5 = X1+X2
        temp = (B5+8)/2**4
        return temp, B5

    def _calculate_pressure(self, B5):
        """
        Calculates pressure in hPa.
        """
        try:
            UP = (self.UP_raw[0] << 16 + self.UP_raw[1] << 8 + self.UP_raw[2]) >> (8 - self.oversampling_setting)
        except Exception:
            raise
        B6 = B5-4000
        X1 = (self._B2*(B6**2/2**12))/2**11
        X2 = self._AC2*B6/2**11
        X3 = X1+X2
        B3 = ((int((self._AC1*4+X3)) << self.oversample_setting)+2)/4
        X1 = self._AC3*B6/2**13
        X2 = (self._B1*(B6**2/2**12))/2**16
        X3 = ((X1+X2)+2)/2**2
        B4 = abs(self._AC4)*(X3+32768)/2**15
        B7 = (abs(UP)-B3) * (50000 >> self.oversample_setting)
        if B7 < 0x80000000:
            pres = (B7*2)/B4
        else:
            pres = (B7/B4)*2
        X1 = (pres/2**8)**2
        X1 = (X1*3038)/2**16
        X2 = (-7357*pres)/2**16
        pres = (pres+(X1+X2+3791)/2**4)/100
        return pres

    def _get_calib_coefficents(self):
        """
        Obtains calibration data from memory, specified in the datasheet.
        """
        try:
            self.AC1 = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xAA, 2))[0]
            self.AC2 = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xAC, 2))[0]
            self.AC3 = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xAE, 2))[0]
            self.AC4 = ustruct.unpack(">H", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xB0, 2))[0]
            self.AC5 = ustruct.unpack(">H", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xB2, 2))[0]
            self.AC6 = ustruct.unpack(">H", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xB4, 2))[0]
            self.B1 = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xB6, 2))[0]
            self.B2 = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xB8, 2))[0]
            self.MB = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xBA, 2))[0]
            self.MC = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xBC, 2))[0]
            self.MD = ustruct.unpack(">h", self.i2cbus.readfrom_mem(
                self._BMP_ADRESS, 0xBE, 2))[0]
        except Exception:
            raise
