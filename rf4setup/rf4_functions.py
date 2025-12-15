#!/usr/bin/env python
# RF4 functions for RF Sensor Configuration Tools
#-----------------

import sys
import serial
from time import sleep
from math import log


def helpmessage(AppName):
    print("\nRF Sensor Configuration Tool for either RF2 / RF4")
    print(f"\nUsage: {AppName}  deviceID  [newDeviceID or '-']  [interval]\n")
    print("deviceID    = current device ID of the sensor")
    print("newDeviceID =  (Optional) Assign specific newDeviceID. (Leaving this blank will auto-assign a newDeviceID).")
    print("        Use '-' to auto-assign a value for newDeviceID when setting the Interval manually")
    print("interval    = Optional, set polling interval in minutes (default is 5)")
    exit()
    sys.exit(1)
    
def is_raspberry_pi():
    """
    Returns True if running on a Raspberry Pi, False otherwise.
    """
    import platform
    try:
        with open('/proc/cpuinfo', 'r') as cpuinfo:
            info = cpuinfo.read()
            if 'Raspberry Pi' in info or 'BCM' in info:
                return True
    except Exception:
        pass
    # Additional check for platform
    if platform.system() == 'Linux':
        try:
            with open('/etc/os-release', 'r') as f:
                if 'raspbian' in f.read().lower():
                    return True
        except Exception:
            pass
    return False

baud = 9600                 # baud rate
if is_raspberry_pi():
    port = '/dev/serial0'       # serial URF port on this computer
else:
    port = 'com6'

ser = serial.Serial(port, baud)
ser.timeout = 0
#-----------------
#
# Send a request command and wait for response
#----------------
def request(device, request, retry, rf4=1):
    poll = 1
    n = 0
    while poll == 1 and n < retry:
        sleep(n)            # sleep longer each time I don't get a response
        ser.flushInput()    # clear input buffer
        if rf4 == 1:
            print('Sending RF4:  ' + device + " command " + request[:7])
            ser.write(('b' + device + request[:7]).encode())  # write as binary
        else:
            print('Sending RF2:  ' + device + " command " + request)
            ser.write(('a' + device + request).encode())
        print("Waiting for response...")
        response = getresponse(device, rf4)
        if len(response) > 1:
            if rf4 == 0:
                response = response[3:12]
            else:
                response = response[5:12]
            poll = 0
        n += 1
        sleep(0.5)
    #print('Request got: ' + str(response))
    return response

#----------------
# Get response from serial port, or timeout
#----------------
def getresponse(devid,rf4=1):
    global  ser
    timeout = 15
    message = '2'
    messagecount = 0
    while timeout > 0:
        if ser.inWaiting() >= 12:
            sleep(0.05)
            try:
                ch = ser.read(12).decode()
                #print("getresponse debug: received message " + ch + " looking for " + devid + " mode " + str(rf4))
            except:
                print("ERROR: Invalid to read response")
                ch = ''
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
                    #print("getresponse debug: a message"+ ch[1:3] + " looking for " + devid )
                    if ch[1:3] == devid:
                        message = ch[0:12]
                        return message
                    else:
                        message = '0'
                else:
                    message = '1'
                    #print("getresponse debug: Not 'a' in response reading next char...")
        else:
            sleep(0.08)
        timeout -= 1
        
    if timeout == 0:
        print("Timeout for get response")
    ser.flushInput()
    return message

#----------------
# Wait for STARTED message from device
# issue REBOOT if timeout
#----------------
def getstarted(devid, rf4=1):      # wait for the STARTED message from devid
    import time
    t = 1
    start_time = time.time()
    while t == 1:
        if time.time() - start_time > 60:
            print("Timeout waiting for STARTED message.")
            exit()
        if ser.inWaiting() >= 12:
            try:
                firstchar = ser.read().decode()
            except:
                firstchar = ''
            #print("getstarted debug First char:", firstchar)
            if rf4 == 0:
                if firstchar == 'a':
                    message = 'a'
                    sleep(0.1)
                    next_char = ser.read(2).decode()
                    #print("getstarted debug device id:", next_char)
                    if next_char == devid:
                        gotresponse = ser.read(9).decode()
                        #print("getstarted debug gotresponse:", gotresponse)
                        if 'STARTED' in gotresponse:
                            t = 0
            else:
                if firstchar == 'b':
                    message = 'b'
                    sleep(0.1)
                    next_char = ser.read(4).decode()
                    #print("getstarted debug device id:", next_char)
                    if next_char == devid:
                        gotresponse = ser.read(7).decode()
                        #print("getstarted debug gotresponse:", gotresponse)
                        if 'STARTED' in gotresponse:
                            t = 0
        #ser.flushInput()
        sleep(0.1)
        # Try WAKE every 15 seconds
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed > 0:
            print("Timeout waiting for STARTED message, try Wake. "+str(elapsed) + " seconds")
            response = request(devid, 'REBOOT', 1, rf4)
    print("Got STARTED message received from " + devid)
    return
#----------------
# Verify device ID format
#----------------
def verify_deviceid(deviceid, rf4=1):
    """
    Verifies that the device ID is valid:
    - For rf4=0: must be 2 characters, each 0-9, a-z, or A-Z
    - For rf4=1: must be 4 characters, each 0-9, a-z, or A-Z
    Returns True if valid, False otherwise.
    """
    charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if rf4 == 0:
        if len(deviceid) != 2:
            return False
        for c in deviceid:
            if c not in charset:
                return False
    else:
        if len(deviceid) != 4:
            return False
        for c in deviceid:
            if c not in charset:
                return False
    return True

#----------------
# Perform any necessary cleanup or finalization tasks before closing the program.
#----------------
def programcloseout(newdevid, rf4=1, relay=0):
    """
    Perform any necessary cleanup or finalization tasks before closing the program.
    """

    if relay == 1:
        response = request(newdevid, 'RBSON', 3, rf4)   # sleep cycle
        print("RECEIVED : ", response)
        if 'RBSON' not in response:
            print('INVALID RESPONSE - ' + response)
            exit()
    else:
        response = request(newdevid, 'RBSOFF', 3, rf4)   # sleep cycle
        print("RECEIVED : ", response)
        if 'RBSOFF' not in response:
            print('INVALID RESPONSE - ' + response)
            exit()
            
    response = request(newdevid, 'VERSION', 3, rf4)
    print("RECEIVED : ", response)

    #quit()  #debug stop point
    sleep(2)
    response = request(newdevid, 'CYCLE', 3, rf4)
    print("RECEIVED : ", response)
    if 'CYCLE' not in response:        
        response = request(newdevid, 'CYCLE', 3, rf4)
        print("RECEIVED : ", response)
        

#----------------
# Program sensor using RF2 protocol
#----------------
def programsensorR2(devid, newdevid, interval, rf4, type):
    response = request(devid, 'WAKE', 8, rf4)
    print("RECEIVED : ", response)
    if 'WAKE' not in response and 'STARTED' not in response:
        print('1 INVALID RESPONSE - ' + str(response))
        exit()

    if devid != newdevid:
        response = request(devid, 'CHDEVID' + newdevid, 3, rf4)
        print("RECEIVED : ", response)
        if 'CHDEVID' + newdevid not in response:
            print('INVALID RESPONSE - ' + str(response) + '<>' + 'CHDEVID' + newdevid)
            exit()

    type = 'TYPE' + str(type) + '-----'
    response = request(newdevid, type[0:9], 3, rf4)
    print("RECEIVED : ", response)
    if type[0:9] not in response:
        print('2 INVALID RESPONSE - ' + str(response))
        exit()

    response = request(newdevid, 'INTVL' + str(interval).zfill(3) + '-', 3, rf4)
    if 'INTVL' + str(interval).zfill(3)  not in response:
        print('INVALID RESPONSE - ' + str(response))
        exit()

    response = request(newdevid, 'NOMSG1---', 3, rf4)
    print("RECEIVED : ", response)
    if 'NOMSG1' not in response:
        print('INVALID RESPONSE - ' + str(response))
        exit()

#----------------
# Program sensor using RF4 protocol
#----------------
def programsensorR4(devid, newdevid, interval, rf4, type):
    response = request(devid, 'WAKE', 8, rf4)
    print("RECEIVED : ", response)
    if 'WAKE' not in response and 'STARTED' not in response:
        print('1 INVALID RESPONSE - ' + str(response))
        exit()

    if devid != newdevid:
        response = request(devid, 'CID' + newdevid, 3, rf4)
        print("RECEIVED : ", response)
        if 'CID' + newdevid not in response:
            print('INVALID RESPONSE - ' + str(response) + '<>' + 'CID' + newdevid)
            exit()

    type = 'TYPE' + str(type) + '-----'
    response = request(newdevid, type[0:7], 3, rf4)
    print("RECEIVED : ", response)
    if type[:7] not in response:
        print('2 INVALID RESPONSE - ' + str(response))
        exit()

    response = request(newdevid, 'INVL' + str(interval).zfill(3) + '-', 3, rf4)
    print("RECEIVED : ", response)
    if 'INVL' + str(interval).zfill(3) not in response:
        print('INVALID RESPONSE - ' + str(response))
        exit()

    response = request(newdevid, 'NOMSG1-', 3, rf4)
    print("RECEIVED : ", response)
    if response != 'NOMSG1-':
        print('INVALID RESPONSE - ' + str(response))
        exit()
        
#----------------
# Increment RF4 device ID
#----------------
def increment_deviceid(deviceid):
    """
    Increments the last 3 characters of a device ID using 0-9, a-z, A-Z.
    Rolls over from 'ZZZ' to '000'.
    """
    charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    print("increase device id ",deviceid)
    if len(deviceid) != 3:
        raise ValueError("Device ID must be 3 characters")
    # Convert to index
    idx = [charset.find(c) for c in deviceid]
    if any(i == -1 for i in idx):
        raise ValueError("Invalid character in device ID")
    # Increment last character
    idx[2] += 1
    if idx[2] >= len(charset):
        idx[2] = 0
        idx[1] += 1
        if idx[1] >= len(charset):
            idx[1] = 0
            idx[0] += 1
            if idx[0] >= len(charset):
                idx[0] = 0
    return charset[idx[0]] + charset[idx[1]] + charset[idx[2]]

#----------------
# Read device ID from a text file
#----------------
def read_deviceid_from_file():
    """
    Reads the device ID from a text file.
    Returns the device ID as a string, stripped of whitespace and newlines.
    """
    filename="nextdevid.txt"
    try:
        with open(filename, "r") as f:
            deviceid = f.readline().strip()
            if not deviceid:
                print("No device ID found in file, starting at default D100.")
                deviceid = "D100"
        return deviceid
    except Exception as e:
        print("Error reading device ID from file:", e)
        return None

#----------------
# Save next device ID to a text file
#----------------
def save_deviceid_to_file(newdevid,filename):
    """
    Saves the new device ID to a text file.
    Increment last 3 characters and saved the next device ID to file
    """
    if not filename:
        print("No filename provided")
        quit()
    deviceidupper = newdevid[:1]
    deviceid = newdevid[1:]
    print("Saving new device ID:", newdevid)
    deviceid = increment_deviceid(deviceid)
    #print("debug Incremented device ID:", deviceid)
    newdevid = deviceidupper + deviceid
    #print("debug New Id is: ", newdevid)
    try:
        with open(filename, "w") as f:
            f.write(str(newdevid).strip() + "\n")
        print("Saved new device ID to file:", newdevid)
    except Exception as e:
        print("Error saving device ID to file:", e)
