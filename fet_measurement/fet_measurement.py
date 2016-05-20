# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 15:11:58 2015

@author: Sergey
"""

import logging
import os
import shutil
import sys
import time
import winsound
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from keithley6487 import Keithley6487
from ni6030e import NI6030E


import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpldatacursor import datacursor

form_class = uic.loadUiType("form.ui")[0]                 # Load the UI


class MyWindowClass(QMainWindow, form_class):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.pushButton_iv.clicked.connect(self.measure_iv)
        self.pushButton_it.clicked.connect(self.measure_it)
        self.pushButton_idvd.clicked.connect(self.measure_idvd)
        self.pushButton_idvg.clicked.connect(self.measure_idvg)
        self.pushButton_iv_save.clicked.connect(self.save_iv)
        self.pushButton_it_save.clicked.connect(self.save_it)
        self.pushButton_idvd_save.clicked.connect(self.save_idvd)
        self.pushButton_idvg_save.clicked.connect(self.save_idvg)
        self.pushButton_stop.clicked.connect(self.stop_measurement)

        # save config
        self.pushButton_iv_save_config.clicked.connect(self.save_config_iv)
        self.pushButton_idvd_save_config.clicked.connect(self.save_config_idvd)
        self.pushButton_idvg_save_config.clicked.connect(self.save_config_idvg)
        # recall config
        self.pushButton_iv_recall_config.clicked.connect(self.recall_config_iv)
        self.pushButton_idvd_recall_config.clicked.connect(self.recall_config_idvd)
        self.pushButton_idvg_recall_config.clicked.connect(self.recall_config_idvg)

        self.saved_configs = {}

        self.pushButton_folder.clicked.connect(self.selectFile)
        self.stop_engaged = False

        # hardware setup
        self.daq = NI6030E()
        self.daq.set_voltage_ao0(0)
        self.ammeter = Keithley6487()
        self.ammeter.voltage(0)
        self.ammeter.voltage_source_state(True)

    def get_vd_values(self):
        self.vd_start = self.doubleSpinBox_vd_start.value()
        self.vd_step = self.doubleSpinBox_vd_step.value()
        self.vd_stop = self.doubleSpinBox_vd_stop.value()
        self.vd_steps = calculate_steps(self.vd_start, self.vd_step,
                                        self.vd_stop)

    def get_vg_values(self):
        self.vg_start = self.doubleSpinBox_vg_start.value()
        self.vg_step = self.doubleSpinBox_vg_step.value()
        self.vg_stop = self.doubleSpinBox_vg_stop.value()
        self.vg_steps = calculate_steps(self.vg_start, self.vg_step,
                                        self.vg_stop)

    def selectFile(self):
        self.lineEdit_folder.setText(QFileDialog.getExistingDirectory(
                                     directory='F:/Users Data'))

    def save_config_iv(self):
        self.save_config('iv')

    def save_config_idvd(self):
        self.save_config('idvd')

    def save_config_idvg(self):
        self.save_config('idvg')

    def recall_config_iv(self):
        self.recall_config('iv')

    def recall_config_idvd(self):
        self.recall_config('idvd')

    def recall_config_idvg(self):
        self.recall_config('idvg')

    def recall_config(self, variant):
        if variant not in self.saved_configs:
            return
        config = self.saved_configs[variant]
        self.doubleSpinBox_vd_start.setValue(config['vd_start'])
        self.doubleSpinBox_vd_step.setValue(config['vd_step'])
        self.doubleSpinBox_vd_stop.setValue(config['vd_stop'])
        self.doubleSpinBox_vg_start.setValue(config['vg_start'])
        self.doubleSpinBox_vg_step.setValue(config['vg_step'])
        self.doubleSpinBox_vg_stop.setValue(config['vg_stop'])

    def save_config(self, variant):
        self.get_vd_values()
        self.get_vg_values()
        self.saved_configs[variant] = {'vd_start': self.vd_start,
                                       'vd_step': self.vd_step,
                                       'vd_stop': self.vd_stop,
                                       'vg_start': self.vg_start,
                                       'vg_step': self.vg_step,
                                       'vg_stop': self.vg_stop,
                                       }

    def save_iv(self):
        filename = os.path.join(self.lineEdit_folder.text(),
                                self.lineEdit_filename.text())
        self.data_iv.to_csv(filename + '.csv')
        self.data_iv.to_msgpack(filename + '.msgpack')
        shutil.copy('measurement_iv.png', filename + '_iv.png')
        self.textBrowser.append('I-V data saved')

    def save_it(self):
        filename = os.path.join(self.lineEdit_folder.text(),
                                self.lineEdit_filename.text())
        self.data_it.to_csv(filename + '.csv')
        self.data_it.to_msgpack(filename + '.msgpack')
        shutil.copy('measurement_it.png', filename + '_it.png')
        self.textBrowser.append('I-t data saved')

    def save_idvd(self):
        filename = os.path.join(self.lineEdit_folder.text(),
                                self.lineEdit_filename.text())
        self.data_idvd.to_csv(filename + '.csv')
        self.data_idvd.to_msgpack(filename + '.msgpack')
        shutil.copy('measurement_idvd_no_legend.png',
                    filename + '_idvd_no_legend.png')
        shutil.copy('measurement_idvd.png', filename + '_idvd.png')
        self.textBrowser.append('Id-Vd data saved')

    def save_idvg(self):
        filename = os.path.join(self.lineEdit_folder.text(),
                                self.lineEdit_filename.text())
        self.data_idvg.to_csv(filename + '.csv')
        self.data_idvg.to_msgpack(filename + '.msgpack')
        shutil.copy('measurement_idvg_log.png', filename + '_idvg_log.png')
        shutil.copy('measurement_idvg.png', filename + '_idvg.png')
        self.textBrowser.append('Id-Vg data saved')

    def measure_iv(self):
        self.get_vd_values()
        self.textBrowser.append('Measuring I-V from ' + str(self.vd_start) +
                                'V to ' + str(self.vd_stop) + ' V')
        vd_values = np.linspace(self.vd_start, self.vd_stop, num=self.vd_steps,
                                endpoint=True)
        id_values = np.zeros_like(vd_values)
#        self.measure_current()
        for i, vd in np.ndenumerate(vd_values):
            self.set_voltage_vd(vd)
            id_values[i] = self.measure_current()
            if self.stop_engaged:
                print('stop')
                self.stop_engaged = False
                break

            self.update_progress((i[0] + 1.0)/self.vd_steps)
        self.set_voltage_vd(0)
        self.textBrowser.append('Measurement completed')
        data = pd.DataFrame({'Voltage': vd_values, 'Current': id_values})
        data.set_index('Voltage', inplace=True)
        self.data_iv = data
        data.to_csv('measurement_iv.csv')
        data.to_msgpack('measurement_iv.msgpack')
        ax = data.plot()
        datacursor(ax)
#        datacursor(display='single', draggable=True)
        winsound.Beep(750, 1000)
        fig = ax.get_figure()
        fig.savefig('measurement_iv.png')
        plt.show()


    def measure_it(self):
        """Measure current vs time."""
        vd = self.doubleSpinBox_vd_steady.value()
        vg = self.doubleSpinBox_vg_steady.value()
        self.textBrowser.append('Measuring I-t @ Vd=' + str(vd) +
                                'V, Vg=' + str(vg) + 'V')
        self.set_voltage_vd(vd)
        self.set_voltage_vg(vg)
        total_time = self.doubleSpinBox_time_steady.value()
        data = pd.DataFrame()
        self.ammeter.voltage_source_state(True)
        t_start = time.clock()
        elapsed = 0
        while (elapsed <= total_time):
            data = data.append({'Current': self.measure_current(),
                               'Time': elapsed}, ignore_index=True)

            elapsed = time.clock() - t_start

            self.update_progress(elapsed/total_time)

            if self.stop_engaged:
                print('stop')
                self.stop_engaged = False
                break
        self.set_voltage_vd(0)
        self.set_voltage_vg(0)
        self.ammeter.voltage_source_state(False)
        self.textBrowser.append('Measurement completed')
        data.set_index('Time', inplace=True)
        self.data_it = data
        data.to_csv('measurement_it.csv')
        data.to_msgpack('measurement_it.msgpack')
        ax = data.plot()

        winsound.Beep(750, 1000)
        fig = ax.get_figure()
        fig.savefig('measurement_it.png')
        plt.show()


    def update_progress(self, progress):
        """Set progress value based on fraction between 0 and 1."""
        self.progressBar.setValue(int(np.ceil(100*progress)))
#        self.repaint()
        QApplication.processEvents()

    def measure_idvd(self):
        self.get_vd_values()
        self.get_vg_values()
        self.textBrowser.append('Measuring Id-Vd for Vd=' +
                                str(self.vd_start) + 'V...' +
                                str(self.vd_stop) + 'V and Vg=' +
                                str(self.vg_start) + 'V...' +
                                str(self.vg_stop) + 'V')
        vd_values = np.linspace(self.vd_start, self.vd_stop, num=self.vd_steps,
                                endpoint=True)
        vg_values = np.linspace(self.vg_start, self.vg_stop, num=self.vg_steps,
                                endpoint=True)
        data = pd.DataFrame()
        self.ammeter.voltage_source_state(True)
        for vg in vg_values:
            self.set_voltage_vg(vg)
            for vd in vd_values:
                self.set_voltage_vd(vd)
                data = data.append({'Id': self.measure_current(),
                                    'Vd': vd, 'Vg': vg}, ignore_index=True)
                if self.stop_engaged:
                    break
                self.update_progress(len(data)/(self.vd_steps*self.vg_steps))
            if self.stop_engaged:
                self.stop_engaged = False
                break
        self.set_voltage_vd(0)
        self.set_voltage_vg(0)
        self.ammeter.voltage_source_state(False)
        self.textBrowser.append('Measurement completed')
        self.data_idvd = data
        data.to_csv('measurement_idvd.csv')
        data.to_msgpack('measurement_idvd.msgpack')
        self.plot_id_vd()
        winsound.Beep(750, 1000)
        plt.show()

    def measure_idvg(self):
        self.get_vd_values()
        self.get_vg_values()
        self.textBrowser.append('Measuring Id-Vg for Vg=' +
                                str(self.vg_start) + 'V...' +
                                str(self.vg_stop) + 'V and Vd=' +
                                str(self.vd_start) + 'V...' +
                                str(self.vd_stop) + 'V')
        vd_values = np.linspace(self.vd_start, self.vd_stop, num=self.vd_steps,
                                endpoint=True)
        vg_values = np.linspace(self.vg_start, self.vg_stop, num=self.vg_steps,
                                endpoint=True)
        data = pd.DataFrame()
        self.ammeter.voltage_source_state(True)

        for vd in vd_values:
            self.set_voltage_vd(vd)
            for vg in vg_values:
                self.set_voltage_vg(vg)
                data = data.append({'Id': self.measure_current(),
                                    'Vd': vd, 'Vg': vg}, ignore_index=True)
                if self.stop_engaged:
                    break
                self.update_progress(len(data)/(self.vd_steps*self.vg_steps))
            if self.stop_engaged:
                self.stop_engaged = False
                break
        self.set_voltage_vd(0)
        self.set_voltage_vg(0)
        self.ammeter.voltage_source_state(False)
        self.textBrowser.append('Measurement completed')
        self.data_idvg = data
        data.to_csv('measurement_idvg.csv')
        data.to_msgpack('measurement_idvg.msgpack')
        self.plot_id_vg()
        winsound.Beep(750, 1000)
        plt.show()


    def stop_measurement(self):
        self.stop_engaged = True

    def set_voltage_vg(self, voltage):
        self.lcdNumber_vg.display(voltage)
        self.ammeter.voltage(voltage)

    def set_voltage_vd(self, voltage):
        self.lcdNumber_vd.display(voltage)
        self.daq.set_voltage_ao0(voltage)

    def measure_current(self):
        current = self.ammeter.current()
        self.lineEdit.setText(str(current))
        return current

    def plot_id_vd(self):
        """Analyze Id-Vd measurement and print the results."""
        # find unique vg values
        data = self.data_idvd
        vg_values = data['Vg'].unique()
        ax = plt.figure()
        # set engineering notation for y axis
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        for vg in vg_values:
            # select only data at this Vg
            data_subset = data.ix[data['Vg'] == vg]
            x = data_subset['Id']
            y = data_subset['Vd']
            plt.plot(y, x, label=('Vg=' + str(vg) + 'V'))

        plt.xlabel('Voltage, V')
        plt.ylabel('Current, A')
        plt.title('Id-Vd')
        plt.savefig('measurement_idvd_no_legend.png', bbox_inches='tight')
        plt.legend(loc="upper left")
        plt.savefig('measurement_idvd.png', bbox_inches='tight')
        return ax

    def plot_id_vg(self):
        """Analyze Id-Vg measurement and print the results."""
        # find unique vd values
        data = self.data_idvg
        vd_values = data['Vd'].unique()
        ax1 = plt.figure()
        # set engineering notation for y axis
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        for vd in vd_values:
            # select only data at this Vd
            data_subset = data.ix[data['Vd'] == vd]
            # run a linear fit on the data subset to get the resistance
            x = data_subset['Id']
            y = data_subset['Vg']

            plt.plot(y, x, label=('Vd=' + str(vd) + 'V'))

        plt.xlabel('Voltage, V')
        plt.ylabel('Current, A')
        plt.title('Id-Vg')
        plt.legend(loc="upper left")
        plt.savefig('measurement_idvg.png', bbox_inches='tight')

        ax2 = plt.figure()
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        for vd in vd_values:
            # select only data at this Vg
            data_subset = data.ix[data['Vd'] == vd]
            x = data_subset['Vg']
            y = data_subset['Id']

            plt.semilogy(x, abs(y), label=('Vd=' + str(vd) + 'V'))
            plt.xlabel('Voltage, V')
            plt.ylabel('Current, A')
        plt.legend(loc="lower right")
        plt.savefig('measurement_idvg_log.png', bbox_inches='tight')

        return ax1, ax2


def calculate_steps(start, step, stop):
        return abs(round((stop-start)/step)) + 1


if __name__ == '__main__':
    # Set global RC params
    mpl.rcParams['figure.dpi'] = 100
    mpl.rcParams['font.size'] = 14
    mpl.rcParams['savefig.dpi'] = 300
    mpl.rcParams['lines.linewidth'] = 2
    mpl.rcParams['savefig.bbox'] = 'tight'
    mpl.rcParams['savefig.transparent'] = True

    logging.basicConfig(
            level=logging.DEBUG,
            filename=(r'error.log'),
            filemode='w')
    app = QApplication(sys.argv)
    myWindow = MyWindowClass(None)
    myWindow.show()
    app.exec_()
