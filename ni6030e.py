# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 16:21:50 2015

@author: Siarhei
"""

import PyDAQmx as mx
import numpy as np

class NI6030E:
    """Interact with the NI6030E DAQ.

    """

    def __init__(self, dev='Dev1/'):
        self.analog_output0 = mx.Task()
        self.analog_output0.CreateAOVoltageChan(dev + 'ao0', '', -10.0, 10.0, mx.DAQmx_Val_Volts, None)
        self.analog_output1 = mx.Task()
        self.analog_output1.CreateAOVoltageChan(dev + 'ao1', '', -10.0, 10.0,
                                                mx.DAQmx_Val_Volts, None)
        self.voltage_data = np.zeros(1, dtype=mx.float64) # array for voltages
        self.read = mx.int32() # how many values were read by the DAQ
        self.voltage_input = mx.Task()

    def set_voltage_ao0(self, voltage):
        """Set voltage on ao0
        """
        self.voltage_data[0] = voltage
        self.analog_output0.WriteAnalogF64(1, True,
                                           mx.DAQmx_Val_WaitInfinitely,
                                           mx.DAQmx_Val_GroupByChannel,
                                           self.voltage_data,
                                           mx.byref(self.read), None)
        return self.read

    def set_voltage_ao1(self, voltage):
        """Set voltage on ao1
        """
        self.voltage_data[0] = voltage
        self.analog_output1.WriteAnalogF64(1, True,
                                           mx.DAQmx_Val_WaitInfinitely,
                                           mx.DAQmx_Val_GroupByChannel,
                                           self.voltage_data,
                                           mx.byref(self.read), None)
        return self.read

    def read_voltage(self, channel):
        """Read voltage on specific channel. Not efficient!!
        Debug use only."""
        voltage_input = mx.Task()
        voltage_input.CreateAIVoltageChan('Dev1/ai' + str(channel), '',
                                          mx.DAQmx_Val_RSE, -10, 10,
                                          mx.DAQmx_Val_Volts, None)
        voltage_input.ReadAnalogF64(1, mx.DAQmx_Val_WaitInfinitely,
                                    mx.DAQmx_Val_GroupByChannel,
                                    self.voltage_data, 1,
                                    mx.byref(self.read), None)
        return self.voltage_data


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Disable the voltage output
        self.set_voltage_ao0(0)
        self.set_voltage_ao1(0)


if __name__ == '__main__':
    with NI6030E() as meter:
        print('Setting voltage on ao0: 1.0V', meter.set_voltage_ao0(1))
        print('Reading voltage on ai1: ', meter.read_voltage(1)[0], 'V')
        print('Setting voltage on ao0: 0.0V', meter.set_voltage_ao0(0))
        print('Reading voltage on ai1: ', meter.read_voltage(1)[0], 'V')
