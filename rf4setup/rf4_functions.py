#!/usr/bin/env python
# RF4 functions for RF Sensor Configuration Tools
#-----------------

import sys
import serial
from time import sleep
from math import log
from rf4_library import verify_deviceid


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
ser.timeout = 0.2

def serial_bytes_waiting(serial_port):
    waiting = getattr(serial_port, "in_waiting", None)
    if callable(waiting):
        waiting = waiting()
    if waiting is None:
        try:
            return serial_port.inWaiting()
        except Exception:
            return 0
    return waiting

def read_exact(serial_port, size, timeout_s=1.0):
    import time
    data = b""
    end_time = time.time() + timeout_s
    while len(data) < size and time.time() < end_time:
        if not data:
            first = serial_port.read(1)
            if not first:
                sleep(0.01)
                continue
            if first not in (b"a", b"b"):
                continue
            data += first
        remaining = size - len(data)
        if remaining <= 0:
            break
        chunk = serial_port.read(remaining)
        if chunk:
            data += chunk
        else:
            sleep(0.01)
    return data
#-----------------
#
# Send a request command and wait for response
#----------------
def request(device, requestmsg, retry, rf4=1):
    poll = 1
    n = 0
    while poll == 1 and n < retry:
        sleep(n)            # sleep longer each time I don't get a response
        ser.flushInput()    # clear input buffer
        if rf4 == 1:
            print('Sending RF4:  ' + device + " command " + requestmsg[:7])
            ser.write(('b' + device + requestmsg[:7]).encode())  # write as binary
        else:
            print('Sending RF2:  ' + device + " command " + requestmsg)
            ser.write(('a' + device + requestmsg).encode())
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
    #print('response debug: Request got: ' + str(response))
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
        #print(f"getresponse debug: Timeout = {timeout}, bytes waiting = {serial_bytes_waiting(ser) }")
        if serial_bytes_waiting(ser) >= 1 or ser.timeout:
            sleep(0.02)
            try:
                raw = read_exact(ser, 12, timeout_s=0.5)
                if len(raw) < 12:
                    timeout -= 1
                    continue
                ch = raw.decode(errors="ignore")
                print("getresponse debug: received message ->" + ch + "<- looking for " + devid + " mode " + str(rf4))
            except Exception:
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
                #print("getresponse debug: Not 'b' in response reading next char...")
                
                if ch[0] == 'a':
                    #print("getresponse debug: a message "+ ch[1:3] + " looking for " + devid )
                    if ch[1:3] == devid:
                        message = ch[0:12]
                        #print(f"getresponse debug: matched device id {devid} returning message ->" + message + "<-")
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
    sendbreak = 0
    while t == 1:
        if time.time() - start_time > 60:
            #print("getstarted debug Timeout waiting for STARTED message.")
            exit()
        received = getresponse(devid, rf4)
        if len(received) >= 12:
            try:
                firstchar = received[0]
            except:
                firstchar = ''
            #print("getstarted debug First char:", firstchar)
            if rf4 == 0:
                if firstchar == 'a':
                    message = 'a'
                    sleep(0.1)
                    next_char = received[1:3]
                    #print("getstarted debug device id:", next_char)
                    if next_char == devid:
                        gotresponse = received[3:10]
                        #print("getstarted debug gotresponse:", gotresponse)
                        if 'STARTED' in gotresponse:
                            t = 0
            else:
                if firstchar == 'b':
                    message = 'b'
                    sleep(0.1)
                    next_char = received[1:5]
                    #print("getstarted debug device id:", next_char)
                    if next_char == devid:
                        gotresponse = received[5:12]
                        #print("getstarted debug gotresponse:", gotresponse)
                        if 'STARTED' in gotresponse:
                            t = 0
        #ser.flushInput()
        sleep(0.1)
        # Try WAKE every 15 seconds
        elapsed = int(time.time() - start_time)
        #print(f"getstarted debug elapsed time: {elapsed} seconds {elapsed % 15}")
        #if elapsed > 15  and elapsed > 0:
        print("Timeout waiting for STARTED message, try Wake. "+str(elapsed) + " seconds")
        response = request(devid, 'REBOOT', 1, rf4)
        sleep(1.5) # wait a moment for reboot to take effect before looking for STARTED message again
            
    #print("Got STARTED message received from " + devid)
    return

#----------------
# Perform any necessary cleanup or finalization tasks before closing the program.
#----------------
def programcloseout(newdevid, rf4=1, relay=0):
    """
    Perform any necessary cleanup or finalization tasks before closing the program.
    """

    if relay == 1:
        response = request(newdevid, 'RBSON', 3, rf4)   # Send update on Button
        if 'RBSON' not in response:
            print('INVALID RESPONSE - ' + response)
            exit()
    else:
        response = request(newdevid, 'RBSOFF', 3, rf4)   # Don't update on Button
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
    #charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # 1/13/2026 Changed to uppercase only for RF4 device IDs
    charset = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
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
