#!/usr/bin/env python
"""
rfsensor.py v26 PrivateEyePi RF Sensor Interface
---------------------------------------------------------------------------------
 Works conjunction with host at www.privateeyepi.com
 Visit projects.privateeyepi.com for full details

 J. Evans October 2013
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 Revision History
 V1.00 - Release
 V2.00 - Incorporation of rules functionality
 V3.00 - Incorporated Button B logic
 V3.01 - High CPU utilization fixed
 V9    - Rule release
 V10   - Added support for the BETA single button power saving wireless switch
       - Functionality added for wireless temperature and humidity sensor
 V11   - Fixed a bug with negative readings from a DHT22 sensor
 V13   - Publish temperature to LCD
 V14   - Added auto sensor creation on the server, dropped support for obsolete two button sensors
 V15   - Added token based authentication
 V16   - Removed delay to speed up serial polling
 V17   - Added functionality for Light sensors
 V18   - Fixed bug wireles switch BUTTONON and BUTTONOFF sensing same state
 V20   - Changed STATEON STATEOFF to not trigger rules or log on the server
 V21   - Added support for BME280 Temperature, Humidity and Air Pressure
 V22   - Further modifications for BME280
 V23   - Added supprt for local automation rules
 V24   - Added support for BME280
 V25   - Bug Fixes
 V26   - Updated to support Python 3
 v27   - Update tested for RF4 support add started messages
 -----------------------------------------------------------------------------------
"""

import globals
import time
import sys
from threading import Thread
from alarmfunctionsr import UpdateHostThread
from time import sleep
from rflib import rf2serial
from rflib import fetch_messages
from rflib import automation
from rflib import getMessage
import rflib

def dprint(message):
  if (globals.PrintToScreen):
    print (message)

def ProcessMessage(value, DevId, PEPFunction, type):

  # Notify the host that there is new data from a sensor (e.g. door open)
  hostdata =[]

  if (type==3 or type==5 or type==6) and globals.Farenheit: #Do Fahrenheit conversion
        value = float(value)*1.8+32
        value = round(value,2)
  DevId = formatDeviceID(type, DevId)
  hostdata.append(DevId)
  hostdata.append(value)
  if PEPFunction==22: #Battery
      MaxVoltage=3
      for z in range (0,len(globals.VoltageList)):
        if globals.VoltageList[z] == int(DevId):
          MaxVoltage=globals.MaxVoltage[z]
      hostdata.append(MaxVoltage) #MaxVoltage
  if PEPFunction==37: #Temperature or Analog
      if type==3 or type==5 or type==6: #Temperature
          if globals.Farenheit:
            hostdata.append("1") #F
          else:
            hostdata.append("0") #C
      if type==4 or type==10 or type==7 or type==8: #Analog sensors
          hostdata.append("2")
  rt=UpdateHostThread(PEPFunction,hostdata)

  automation(value, DevId)

  return(0)

def formatDeviceID(type, devID):
    if type==1: #Button
      return(globals.BUTTONPrefix+devID)
    if type==2: #Button state
      return(globals.BUTTONPrefix+devID)
    if type==5: #Temp B
      return(globals.TMPBPrefix+devID)
    if type==6: #Temp C
      return(globals.TMPCPrefix+devID)
    if type==7: #Humidity
      return(globals.HUMPrefix+devID)
    if type==8: #Pressure
      return(globals.PRESPrefix+devID)
    if type==10:#Analog B
      return(globals.ANABPrefix+devID)
    return(devID);

def queue_processing():
  while (True):
    fetch_messages(1);
    while len(rflib.processing_queue)>0:
        message = getMessage()
        if message.sensordata != "":
            dprint(time.strftime("%c")+ " " + message.devID+message.data)
            ProcessMessage(message.sensordata, message.devID, message.PEPFunction, message.type)
    sleep(0.2)
    if rflib.event.is_set():
          break

def main():
    globals.init()
    rflib.init()

    dprint("JemRF RF Sensor Interface v27 Starting. ")
    a=Thread(target=rf2serial, args=())
    a.start()

    dprint("Started Serial Interface")
    b=Thread(target=queue_processing, args=())
    b.start()
    dprint("Started Message Processing Thread")
    # Wait for the serial interface to start
    while not rflib.event.is_set():
      try:
          if rflib.timer!=0:
            automation(0,0)
          sleep(1)
      except KeyboardInterrupt:
          rflib.event.set()
          break

if __name__ == "__main__":
    try:
      main()
    except Exception as e:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print (message)
      print (e)
      rflib.event.set()
    finally:
      rflib.event.set()
      exit()








