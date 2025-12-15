#!/usr/bin/env python
# Converted to support python 2 or 3
# Update add error trap, deviceId validatation, RF4 support
import sys
from threading import Thread
#from bme280 import process_bme_reading
from rflib import rf2serial, fetch_messages, request_reply
import rflib
from time import sleep
import time

def main():
  global response_ind
  try:
      rflib.init()

      #start serial processing thread
      a=Thread(target=rf2serial, args=())
      a.start()
      
           # Validate device ID
      try: 
        if (sys.argv[2]=="-V" or sys.argv[2]=="-v"):
          command=sys.argv[1]
        else:
          deviceid = sys.argv[1]     
          if (len(deviceid) != 2 and len(deviceid) !=4) or not deviceid.isalnum():
            quit()
          rf4=0
          if len(deviceid) == 4:
              rf4=1
          if not verify_deviceid(deviceid, rf4):
              raise Exception("ERROR: Device ID must be two or four alphanumeric characters (0-9, a-z,A-Z).")

          # Test if argv[2] contains 'CID'
          if len(deviceid) > 2:   
            # Replace any lowercase 'cid' with uppercase 'CID' in the command
            cmd_arg = sys.argv[2]
            if 'CID' in cmd_arg.upper():
              cmd_arg = cmd_arg.replace(cmd_arg[cmd_arg.lower().find('cid'):cmd_arg.lower().find('cid')+3], 'CID')
                # Check for 4 characters after 'CID'
              cid_index = cmd_arg.upper().find('CID')
              after_cid = cmd_arg[cid_index+3:]
              if len(after_cid) != 4 or not after_cid.isalnum():
                print("\nERROR: After 'CID' there must be exactly 4 characters.")
                raise Exception()
              command = 'b' + sys.argv[1] + cmd_arg  # Construct command
            else:
              command = 'b' + sys.argv[1] + sys.argv[2].upper()
          else:
            # Replace any case of 'chdevid' with uppercase 'CHDEVID'
            cmd_arg = sys.argv[2]
            if 'CHDEVID' in cmd_arg.upper():
              cmd_arg = cmd_arg.replace(cmd_arg[cmd_arg.lower().find('chdevid'):cmd_arg.lower().find('chdevid')+7], 'CHDEVID')
              # Check for 2 characters after 'CHDEVID'
              chdevid_index = cmd_arg.upper().find('CHDEVID')
              after_chdevid = cmd_arg[chdevid_index+7:]
              if len(after_chdevid) != 2 or not after_chdevid.isalnum():
                print("\nERROR: After 'CHDEVID' there must be exactly 2 characters.")
                raise Exception()
              command='a'+sys.argv[1]+cmd_arg   #
            else:
              command='a'+sys.argv[1]+sys.argv[2].upper()   # Construct command
      except:       
            print("\nERROR: Invalid Command Input.\n")
            print("rf_config.py Version 4.0")     
            print("Valid formats: ")
            print("\trf_config deviceID Command")
            print("\tNOTE: Device ID must be two or four characters (0-9, a-z, A-Z).")
            print("\tAlternate format: ")
            print("\trf_config command -v  RF2 Ex: (a03VERSION -v) or RF4 Ex: (b0300VERSION -v)")
            sys.exit(1)    

      print("SENT     : "+command[1:12] )
      request=request_reply(command)
      if (request.rt==1):
          for x in range(request.num_replies):
              print("RECEIVED : " + str(request.id[x]) + str(request.message[x]))
      else:
          print ("NO REPLY")

  except KeyboardInterrupt:
      rflib.event.set()  #exit

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
