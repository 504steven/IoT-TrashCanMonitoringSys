# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#
# Using pySerial
# ls /dev/tty*    check USB ports
import serial
import re

ser = serial.Serial('COM3', 9600)    #  usbmodem1431101    (Arduino/Genuino Uno)

def get_sensor_data():
    s = str( ser.readline())
    print( s)
    d = re.findall("\d+[\.\d+]*", s)
    # print( d )
    data = [ float(d[0]), float(d[1])]
    print("weight reading: ",data[0], ", distance reading: ", data[1])    # 0-100
    return data
