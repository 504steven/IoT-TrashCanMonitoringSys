# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#Using pySerial
#ls /dev/tty*    check USB ports
import serial;
ser = serial.Serial('/dev/tty.usbmodem1431101', 9600);
while True:
    print (ser.readline());
