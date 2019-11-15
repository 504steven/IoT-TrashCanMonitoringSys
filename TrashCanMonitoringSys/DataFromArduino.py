# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#Using pySerial
#ls /dev/tty*    check USB ports
import serial
import re

# ser = serial.Serial('/COM3', 9600)    #  usbmodem1431101
# data = []
# while True:
#     global data
#     d = re.findall("\d+", ser.readline())
#     data = [ int(d[0]), int(d[1])]
#     print("weight reading: ",data[0], ", distance reading: ", data[1])    # 0-100
#
# def get_sensor_data():
#     return data
