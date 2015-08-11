# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 14:56:17 2015

@author: vishniakou
"""


import time
import subprocess

import win32gui
import win32api
import win32con


class iHR550:

    def __init__(self):
        cmd = ["C:\\Program Files\\Jobin Yvon\\USBSpectrometerControl.exe"]
        self.pipe = subprocess.Popen(cmd, shell=True,
                                     stdin=None, stdout=None, stderr=None)
        time.sleep(8)
        try:
            hwnd = win32gui.FindWindow("ThunderRT6FormDC",
                                       "USBSpectrometerControl")
        except:
            hwnd = win32gui.FindWindow("ThunderRT6FormDC",
                                       "IHR 550 [ iHR VER 1.3.22]")
        button = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6CommandButton",
                                       "Initialize")
        win32gui.SetWindowText(button, 'Init Filter')
        button2 = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6CommandButton",
                                        "Initialize")
        win32api.SendMessage(button2, win32con.BM_CLICK, 0, 0)
        time.sleep(10)
        self.hwnd = win32gui.FindWindow("ThunderRT6FormDC",
                                        "IHR 550 [ iHR VER 1.3.22]")

    def set_wavelength(self, wavelength):
        wavelength_box(self.hwnd, wavelength)


def main():

    ihr = iHR550()
    ihr.set_wavelength(450)
    time.sleep(10)
    ihr.set_wavelength(500)
    time.sleep(10)
    ihr.set_wavelength(550)
    time.sleep(10)
    ihr.set_wavelength(600)
    time.sleep(10)

    return
#    try:
#        hwnd = win32gui.FindWindow("ThunderRT6FormDC",
#                                   "USBSpectrometerControl")
#    except:
#        hwnd = win32gui.FindWindow("ThunderRT6FormDC",
#                               "IHR 550 [ iHR VER 1.3.22]")
#    button = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6CommandButton",
#                                   "Initialize")
#    win32gui.SetWindowText(button, 'Init Filter')
#    button2 = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6CommandButton",
#                                    "Initialize")
#    win32api.SendMessage(button2, win32con.BM_CLICK, 0, 0)
#
#   The following does not work!
#   edit = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6TextBox", "1000")
#
#    wavelength_box(hwnd, 450)
#    time.sleep(10)
#    wavelength_box(hwnd, 500)
#    time.sleep(10)
#    wavelength_box(hwnd, 700)
#    return hwnd


def wavelength_box(hwnd, wavelength):
    wav = win32gui.FindWindowEx(hwnd, 0, "ThunderRT6Frame",
                                "Wavelength Control")

    def select_edit_boxes(child, wavelength):
        class_name = win32gui.GetClassName(child)
        text = win32gui.GetWindowText(child)
        if class_name == "ThunderRT6TextBox":
            if text == '1000':
                print("Changing to", wavelength, 'nm ...')
                win32gui.SendMessage(child, win32con.WM_SETTEXT, 0,
                                     str(wavelength))
                win32gui.SendMessage(child, win32con.WM_KEYDOWN,
                                     win32con.VK_RETURN, 0)
                win32gui.SendMessage(child, win32con.WM_CHAR,
                                     win32con.VK_RETURN, 0)

    win32gui.EnumChildWindows(wav, select_edit_boxes, wavelength)

    return wavelength


if __name__ == "__main__":
    out = main()
