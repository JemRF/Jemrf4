#!/usr/bin/env python
"""
rf2mqtt.py v3 Serial to MQTT message broker
---------------------------------------------------------------------------------

 J. Evans August 2018
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 Revision History
 V1.00 - Release
 V2.0  - Updated to use common libraries
 V3.0  - Updated for Python 3

 Instructions:

 This application publishes data from RF messages using JSON (example payload below)
 to a topic of [topic]/[device_prefix]_[device id]
 The topic is set in the config below
 The device_prefix is set in the config below
 The device id is the device id of your RF sensor

 Example topic  : "myhome/RF_Device04"
 Example payload: {"TMP": "25.39", "HUM": "60.20"}

"""

import time
import sys
from threading import Thread
import json
from random import randint
from time import sleep
import paho.mqtt.client as paho
from rflib import rf2serial
from rflib import fetch_messages
from rflib import automation
from rflib import getMessage
import rflib

#Configurations===============
DEBUG = True
Fahrenheit = False
mqtt_server = "192.168.2.137" #Enter the IP address of your MQTT server in between the quotes
topic = "myhome"
device_prefix = "RF_Device"
#=============================

def dprint(message):
  if (DEBUG):
    print (message)

def ProcessMessageThread(value, DevId, property):
  try:
      thread.start_new_thread(ProcessMessage, (value, DevId, property ) )
  except:
      print("Error: unable to start thread")

def mqtt_publish(device_id, value, property):
  data = {}
  data[property] = value;
  json_data = json.dumps(data)
  dprint(topic+"/"+device_id+"/"+property + " - " + json_data)
  client = paho.Client("pi_rf_"+str(randint(0, 100)))
  client.connect(mqtt_server, port=1883)
  client.publish(topic+"/"+device_id+"/"+property, json_data,qos=2,retain=True)
  client.disconnect()

def ProcessMessage(value, DevId, property):
# Notify the host that there is new data from a sensor (e.g. door open)
  try:
    dprint("Processing data : DevId="+str(DevId)+",Value1="+str(value))

    DevId=device_prefix+DevId;

    #Send temperature to host
    if property[0:3]=="TMP":
      if Fahrenheit:
          value = value*1.8+32
          value = round(value,2)

    #For Home assistant change STATE to BUTTON so we have one topic for a button sensor
    if property=="STATE":
        property="BUTTON"

    mqtt_publish(DevId, value, property)

  except Exception as e: dprint(e)
  return(0)

def queue_processing():
  while (True):
    fetch_messages(1);
    while len(rflib.processing_queue)>0:
        message = getMessage();
        if message.sensordata != "":
            dprint(time.strftime("%c")+ " " + message.devID+message.data)
            ProcessMessage(message.sensordata, message.devID, message.description)
    sleep(0.2)
    if rflib.event.is_set():
          break

def main():
    rflib.init()

    a=Thread(target=rf2serial, args=())
    a.start()

    b=Thread(target=queue_processing, args=())
    b.start()

    while not rflib.event.is_set():
      try:
          if rflib.timer!=0:
            automation(0,0)
          sleep(1)
      except KeyboardInterrupt:
          rflib.event.set()
          break

if __name__ == "__main__":
  #try:
    main()
  #except Exception as e:
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(e).__name__, e.args)
    print (message)
    print (e)
    rflib.event.set()
  #inally:
    rflib.event.set()
    exit()








