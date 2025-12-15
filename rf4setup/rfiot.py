#!/usr/bin/env python
# Programming RPI IOT HAT for USB
# This program is run from the command line like this: > python [app].py 02 03
# where xx is the default device Id and yy is the new device Id

import sys
import serial
from time import sleep
from math import log
from rf4_functions import *

baud = 9600                 # baud rate
port = '/dev/serial0'       # serial URF port on this computer

ser = serial.Serial(port, baud)
ser.timeout = 0
rf4 = 1  # default to RF4, set to 0 for RF2
#-----------------

def request(device, request, retry):
    poll = 1
    n = 0
    while (poll == 1 and n < retry):
        sleep(n)            # sleep longer each time I don't get a response
        ser.flushInput()    # clear input buffer
        print('Sending: ' + device + " command " + request)
        ser.write(('b' + device + request).encode())  # see if our device is online
        print("Waiting for response...")
        response = getresponse(device)
        if len(response) > 1:
            response = response[5:12]
            poll = 0
        n = n + 1
        sleep(0.5)
    #print(response)
    return response

#----------------

def getresponse(devid):
    global rf4, ser
    timeout = 15
    message = '2'
    messagecount = 0
    while timeout > 0:
        if ser.inWaiting() >= 12:
            sleep(0.05)
            ch = ser.read(12).decode()
            #print("getresponse debug: received message " + ch)
            if rf4 == 1:
                if ch[0] == 'b':
                    #print("getresponse debug: b message"+ ch)
                    if ch[1:5] == devid:
                        message = ch[0:12]
                        return message
                    else:
                        message = '0'
                else:
                    message = '1'
                    #print("getresponse debug: Not 'b' in response reading next char...")
            else:
                if ch[0] == 'a':
                    if ch[1:3] == devid:
                        message = ch[0:12]
                        return message
                    else:
                        message = '0'
                else:
                    message = '1'
                    #print("getresponse debug: Not 'a' in response reading next char...")
        else:
            sleep(0.05)
        timeout -= 1
        
    if timeout == 0:
        print("Timeout for get response")
    ser.flushInput()
    return message

#---------------
def rgetresponse(devid):     # obtain a llap message from devid
    timeout = 10
    message = '2'
    while timeout > 0:
        if ser.inWaiting() >= 12:
            sleep(0.05)
            ch = ser.read(12).decode()
            #print("getresponse debug: received message " + ch)
            #print("Debug: id is " + ch[1:5])
            if ch[0] == 'b':  # llap message start
                if ch[1:5] == devid:
                    message = ch[0:12]
                    return message
                else:
                    message = '0'   # not a message from devid
            else:
                message = '1'   # not a llap formatted message                
                print("Not 'b' in response reading next char...")
            timeout = 0
        else:
            sleep(0.05)
        timeout -= 1
        #print("Timeout for getresponse")
    ser.flushInput()
    return message

#----------------

def getstarted(devid):      # wait for the STARTED message from devid
    import time
    t = 1
    start_time = time.time()
    while t == 1:
        # Exit if timeout exceeds 60 seconds
        if time.time() - start_time > 60:
            print("Error: Timeout waiting for STARTED message.")
            exit()
        if ser.inWaiting() >= 12:
            firstchar = ser.read().decode()
            #print("First char:", firstchar)
            if firstchar == 'b':   # llap message start
                sleep(0.1)
                rdeviceid = ser.read(4).decode()
                #print("Device ID:", rdeviceid)
                if rdeviceid == devid:    # message is from our device
                    if ser.read(7).decode() == 'STARTED':  # devid has started
                        t = 0
        ser.flushInput()
        sleep(0.1)
        # Try WAKE every 15 seconds
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed > 0:
            print("Timeout waiting for STARTED message, try Wake. "+str(elapsed) + " seconds")
            response = request(devid, 'REBOOT', 1)
    return

def programsensor(devid, newdevid):
    global useidinfile
    if not verify_deviceid(devid, 1):
        print("\nERROR: Invalid device ID format ")
        exit()
    if not verify_deviceid(newdevid, 1):
        print("\nERROR: Invalid device ID format ")
        exit()
    
    response = request(devid, 'REBOOT', 1)
    print("RECEIVED : ", response)
    getstarted(devid)       # wait for device to announce itself with STARTED message

    # seek a connection with the device

    response = request(devid, 'CID' + newdevid, 3)   # change id
    print("RECEIVED : ", response)
    if 'CID' + newdevid not in response:
        print('INAVLID RESPONSE - ' + response + '<>' + 'CID' + newdevid)
        exit()

    response = request(newdevid, 'TYPE2--', 3)   # change type
    print("RECEIVED : ", response)
    if 'TYPE2' not in response:
        print('2 INAVLID RESPONSE - ' + response)
        exit()

    response = request(newdevid, 'RSSION-', 3)   # Get Analog Temp from device
    print("RECEIVED : ", response)
    if 'RSSION' not in response:
        print('2 INAVLID RESPONSE - ' + response)
        exit()

    response = request(newdevid, 'VERSION', 3)   # Show FW Version
    print("RECEIVED : ", response)

    response = request(newdevid, 'REBOOT', 5)   # Show FW Version
    print("RECEIVED : ", response)

    if useidinfile:
        save_deviceid_to_file(newdevid,"iotdevid.txt")
    print('END: Gateway Configuration complete as device ' + newdevid)
    

def inputvalid():
    print("\nUsage: rf4iot.py [deviceID] [newDeviceID]\n")
    print("deviceID    = current device ID of the sensor (4 characters)")
    print("newDeviceID = new device ID to assign to the sensor (4 characters)")
    print("NOTE: Device ID must be four characters (0-9, a-z, A-Z).")

def read_iotdevid_from_file(filename="iotdevid.txt"):
    """
    Reads the device ID from a text file.
    Returns the device ID as a string, stripped of whitespace and newlines.
    """
    try:
        with open(filename, "r") as f:
            deviceid = f.readline().strip()
            if not deviceid:
                print("No device ID found in file, starting at default 1410.")
                deviceid = "1410"
        return deviceid
    except Exception as e:
        print("Error reading device ID from file:", e)
        return None

if __name__ == "__main__":   # run the program from the command line
    useidinfile = False
    if len(sys.argv) < 2:
        inputvalid()
        exit()
    deviceid = sys.argv[1]
    if len(sys.argv) < 3:
        newdeviceid = read_iotdevid_from_file()
        #print("debug Using device ID from file:", newdeviceid)
        useidinfile = True
    else:  
        newdeviceid = sys.argv[2]
        
    if len(deviceid) != 4 or len(newdeviceid) != 4:
        print(">>> Invalid device ID format")
        inputvalid()
        exit()
    print("V1 Set Gateway Device ID >>" + deviceid + "<< New Device ID to **" + newdeviceid + "**")

    programsensor(deviceid, newdeviceid)

