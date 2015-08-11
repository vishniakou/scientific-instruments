# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 14:29:22 2014

@author: vishniakou
"""

import time
import configparser
import json

import numpy as np
import pandas as pd
import visa


class Agilent4284A:

    def __init__(self, config_file):
        rm = visa.ResourceManager()
#        resources = rm.list_resources()
        self.inst = rm.open_resource('GPIB0::20::INSTR')
        print(self.query("*IDN?"))
        # Enable the bias voltage output
        self.write("BIAS:STAT ON")
        # Switch to the measurement page
        self.write("DISP:PAGE MEAS")
        print("Trigger source: ", self.query("TRIG:SOUR?"))
        print("Impedance function: ", self.query("FUNC:IMP?"))
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def __enter__(self):
        return self

    @property
    def bias(self):
        return float(self.query('BIAS:VOLT?'))

    @bias.setter
    def bias(self, bias):
        if abs(bias) > 20:
            print('Error: attempted to set |bias| > 10')
            return
        self.write('BIAS:VOLT ' + str(bias))

    @property
    def frequency(self):
        return float(self.query('FREQ?'))

    @frequency.setter
    def frequency(self, frequency):
        if frequency < 20 or frequency > 1E6:
            print('Error: attempted to set frequency at ', frequency, ' Hz')
            print('This value is out of allowed bounds')
            return
        self.write('FREQ ' + str(int(frequency)) + 'HZ')

    @property
    def voltage(self):
        """Get the oscillator's output voltage level."""
        return float(self.query('VOLT?'))

    @voltage.setter
    def voltage(self, voltage):
        if abs(voltage) > 10:
            print('Error: attempted to set voltage > 10V')
            return
        self.write('VOLT ' + str(voltage) + 'V')

    def query(self, cmd):
        """Send arbitrary command to instrument."""
        time.sleep(0.1)
        while True:
            try:
                return self.inst.query(cmd).strip()
            except visa.VisaIOError:
                error = ""
                while '+0,"No error"' not in error:
                    try:
                        error = self.inst.query("SYST:ERR?")
                        print(error)
                    except visa.VisaIOError:
                        continue

    def write(self, cmd):
        """Send arbitrary command to instrument."""
        time.sleep(0.1)
        return self.inst.write(cmd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Disable the bias voltage output
        self.write("BIAS:STAT OFF")
        self.inst.close()

    def measure(self):
        """Perform the measurement."""
        self.write("INIT")
        self.write("TRIG")
        return [float(n) for n in self.query("FETC?").split(',')]

    def measure_cv(self, frequency):
        self.frequency = frequency
        self.voltage = float(self.config.get('c-v', 'oscillation'))
        data = pd.DataFrame(columns=['Voltage', 'Capacitance'])
        start_voltage = float(self.config.get('c-v', 'start'))
        end_voltage = float(self.config.get('c-v', 'stop'))
        num_points = int(self.config.get('c-v', 'number of points'))
        dwell_time = float(self.config.get('c-v', 'dwell time'))
        for bias in np.linspace(start_voltage, end_voltage, num_points):
            self.bias = bias
            time.sleep(dwell_time)
            data_row = self.measure()
            print(bias, 'V ', data_row)
            data = data.append([{'Voltage': bias,
                                 'Capacitance': data_row[0]}])
        data.set_index('Voltage', inplace=True)
        ax = data.plot(title=("Frequency = " + convert_to_prefix(frequency) +
                              "Hz"), y="Capacitance", legend=False)
        ax.set_xlabel('Voltage, V')
        ax.set_ylabel('Capacitance, F')
        # save plot to file
        # save data to file
        filename = ('output/cv_' + convert_to_prefix(frequency) + 'Hz_' +
                    str(self.voltage*1000) + 'mV_' + str(dwell_time) + 's')
        fig = ax.get_figure()
        fig.savefig(filename + '.pdf')
        fig.savefig(filename + '.png')
        data.to_csv(filename + '.csv')
        return data

    def measure_cf(self, bias):
        self.bias = bias
        self.voltage = float(self.config.get('c-f', 'oscillation'))
        data = pd.DataFrame(columns=['Frequency', 'Capacitance'])
        start_freq = int(self.config.get('c-f', 'start'))
        end_freq = int(self.config.get('c-f', 'stop'))
        num_points = int(self.config.get('c-f', 'number of points'))
        dwell_time = float(self.config.get('c-f', 'dwell time'))
        for frequency in np.logspace(np.log10(start_freq),
                                     np.log10(end_freq),
                                     num=num_points):
            self.frequency = frequency
            time.sleep(dwell_time)
            data_row = self.measure()
            print(frequency, 'hz ', data_row)
            data = data.append([{'Frequency': frequency,
                                 'Capacitance': data_row[0]}])
        data.set_index('Frequency', inplace=True)
        ax = data.plot(title=("Bias = " + str(bias) + " V"), y="Capacitance",
                       legend=False)
        ax.set_xlabel('Frequency, Hz')
        ax.set_ylabel('Capacitance, F')
        # save to file
        filename = ('output/cf_' + str(bias) + 'V_' + str(self.voltage*1000) +
                    'mV_' + str(dwell_time) + 's')
        fig = ax.get_figure()
        fig.savefig(filename + '.pdf')
        fig.savefig(filename + '.png')
        data.to_csv(filename + '.csv')
        return data

    def measure_config(self):
        cv = {}
        # c-v measurements
        for frequency in json.loads(self.config.get("c-v",
                                                    "frequencies")):
            cv[frequency] = self.measure_cv(frequency)
        cf = {}
        # c-f measurements
        for bias in json.loads(self.config.get("c-f", "biases")):
            cf[bias] = self.measure_cf(bias)
        return pd.Panel(cv), pd.Panel(cf)


prefixes = ['', 'k', 'M', 'G']


def convert_to_prefix(n):
    n = float(n)
    millidx = max(0, min(len(prefixes)-1,
                         int(np.floor(np.log10(np.abs(n))/3))))
    return "%.0f %s" % (n/10**(3*millidx), prefixes[millidx])


if __name__ == '__main__':
    filename_config = ("cv_measurement_config.txt")
    with Agilent4284A(filename_config) as cvmeter:
        print('Frequency: ' + str(cvmeter.frequency))
        print('Bias: ' + str(cvmeter.bias))
        print('Voltage: ' + str(cvmeter.voltage))
        cv, cf = cvmeter.measure_config()
        # do something with data here, optionally
        print(cv.items)
        print(cf.items)

        # measure multiple biases/frequencies
#        cvmeter.voltage = 0.02
#        cv = cvmeter.measure_cv(1000000)
#        cf_01 = cvmeter.measure_cf(-1)
#        cf_0 = cvmeter.measure_cf(0)
#        cf_1 = cvmeter.measure_cf(1)

#    cv.plot(title="Frequency = 1KHz", y="Capacitance", legend=False)
#    cf_01.plot(logx=True, title="Bias = -1 V", y="Capacitance", legend=False)
#    cf_0.plot(logx=True, title="Bias = 0 V", y="Capacitance", legend=False)
#    cf_1.plot(logx=True, title="Bias = +1 V", y="Capacitance", legend=False)
#    rm = visa.ResourceManager()
#    resources = rm.list_resources()
#    inst = rm.open_resource(resources[0])
#    print(inst.query("*IDN?"))
