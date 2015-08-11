# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 14:56:17 2015

@author: vishniakou
"""


import time
import visa


class Cornerstone260:

    def __init__(self, resource='GPIB0::4::INSTR'):
        rm = visa.ResourceManager()
        self.inst = rm.open_resource(resource)
        self.inst.read_termination = '\n'
        self.inst.write_termination = '\n'
        print(self.inst.query('INFO?'))

    def units(self):
        return self.inst.query('UNITS?')

    def set_wavelength(self, wavelength):
        self.inst.write('GOWAVE ' + str(wavelength))


def main():
    mono = Cornerstone260()
    print('Units are: ' + mono.units())
    time.sleep(1)
    mono.set_wavelength(550)
    time.sleep(5)
    mono.set_wavelength(650)

if __name__ == "__main__":
    out = main()
