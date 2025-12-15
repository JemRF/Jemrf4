#!/usr/bin/env python

import sys
import serial
from time import sleep
from math import log
from rf4_functions import *

#-----------------
# default to RF2
rf4 = 0
#-----------------

def programsensor(devid, newdevid, interval):
    if not verify_deviceid(devid, rf4):
        print("\nERROR: Invalid device ID format ")
        exit()
    if not verify_deviceid(newdevid, rf4):
        print("\nERROR: Invalid device ID format ")
        exit()

    getstarted(devid, rf4)

    if rf4 == 0:
        print("RF2 protocol detected")
        programsensorR2(devid, newdevid, interval, rf4, 1)
    else:
        print("RF4 protocol detected")
        programsensorR4(devid, newdevid, interval, rf4, 1)
    
    sleep(0.5)  # Allow time for device to process the commands
    response = request(newdevid, 'TEMP--', 3, rf4)
    print("RECEIVED : ", response)
    response = getresponse(newdevid,rf4)
    print("RECEIVED : ", response)

    programcloseout(newdevid,rf4,0)
    
    if useidinfile:
        save_deviceid_to_file(newdevid,"nextdevid.txt")
    print('END: Sensor Configuration complete as device ' + newdevid)

if __name__ == "__main__":
    # Check for Python 3
    if sys.version_info[0] < 3:
        print("This script requires Python 3.")
        exit()

    if len(sys.argv) < 2:
        print("Configure RF Thermistor Temperature Sensor")
        helpmessage("rfthermtemp.py")
    if len(sys.argv) < 4:
        interval = 5
    else:
        interval = int(sys.argv[3])

    useidinfile = False
    if len(sys.argv[1]) == 4:
        rf4 = 1
        print("Using RF4 protocol")
        # Test if argv[2] exists
        newid = sys.argv[2] if len(sys.argv) > 2 else "-"
        if len(sys.argv) < 3 or newid == '-':
            newdeviceid = read_deviceid_from_file()
            useidinfile = True
        else:
            newdeviceid = sys.argv[2]
    else:
        try:
            if len(sys.argv) >= 2:
                newdeviceid = sys.argv[2]
            else:
                raise ValueError("New device ID not provided")
        except:
            print("ERROR: New device ID not provided or invalid format.")
            quit()

    print("Configuring Temp sensor with ID >>" + str(sys.argv[1]) +
          "<< to new ID **" + str(newdeviceid) +
          "** with interval " + str(interval) + " min")
    
    programsensor(sys.argv[1], newdeviceid, interval)
