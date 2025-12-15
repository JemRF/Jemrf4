#!/usr/bin/env python
# Updated to python 3
import sys
from threading import Thread
#from bme280 import process_bme_reading
from rflib import rf2serial, fetch_messages, request_reply
import rflib
from time import sleep
import time
import sys, os

def inbound_message_processing():
  try:
    matrix = []
    counter = []
    loopcount = 0
    messagecount =0
    skipped = 0
    while (True):
        sleep(0.2)
        fetch_messages(0);
        while len(rflib.processing_queue)>0:
            message = rflib.processing_queue.pop(0)
            print(time.strftime("%c")+" "+message[0]+" "+message[1])
            try:
               print(int(message[0]))
            except Exception as e:
               print("skipping: ",message[0])
               skipped = skipped + 1
               break
            mtype = message[1][:4]
            index = int(message[0])
            print(time.strftime("%c")+" "+message[0]+" "+mtype)
            messagecount += 1
            if {index :mtype} not in matrix:
               #print("not found")
               matrix.append({index:mtype})
               nindex = len(matrix)
               #print(matrix, nindex)
               counter.append(1)
               #print(counter)
            else:
                #print("found")
                indices = [cindex for cindex, value in enumerate(matrix) if value == {index:mtype}]
                integer_value = int.from_bytes(indices, byteorder='big', signed=False)
                counter[integer_value] += 1
                #print(f"  {index} {mtype} {counter[integer_value-1]} ")
                #print(matrix)
                #print(counter)
            loopcount +=1
            if loopcount > 2:
                cycle = 0
                totalloss = 0
                print("----------------Summary-------------------- Msg Count: ",messagecount,"  Skipped = ",skipped)
                #while cycle < len(counter):
                #print(f" {matrix[cycle]} count {counter[cycle]} ")
                all_keys = [key for d in matrix for key in d.keys()]
                unique_keys = list(set(all_keys))
                #print(unique_keys)
                subcycle = 0
                #print("---------------------------------------")
                while subcycle < len(unique_keys)-1:
                    filtered_list = [d for d in matrix if unique_keys[subcycle] in d]
                    print (f" Filtered List {filtered_list}")
                    #print("-------subcycle---------")
                    awakecount = 0
                    sleepcount = 0
                    tmpacount = 0
                    tmpccount = 0
                    for subset in filtered_list:
                        #print(subset, end=" ")
                        #print (unique_keys[subcycle], end=" ")
                        msgvalue = subset[unique_keys[subcycle]]
                        #print("------subset----------")
                        indices = [cindex for cindex, value in enumerate(matrix) if value == subset]
                        integer_value = int.from_bytes(indices, byteorder='big', signed=False)
                        #print(integer_value, end=" ")
                        #print(counter[integer_value])
                        if msgvalue == "AWAK" :
                            awakecount = counter[integer_value]
                            #print(f"awake count {counter[integer_value]}")
                        if msgvalue == "SLEE" :
                            sleepcount = counter[integer_value]
                            #print(f"sleep count {counter[integer_value]}")
                        if msgvalue == "TMPC" :
                            tmpccount = counter[integer_value]
                            #print(f"tempc count {counter[integer_value]}")
                        if msgvalue == "TMPA" :
                            tmpacount = counter[integer_value]
                            #print(f"tempa count {counter[integer_value]}")

                    #totalloss = totalloss + awakecount + sleepcount + tmpccount + tmpacount
                    if abs(awakecount - sleepcount) > 0:
                        print("Missed Wake-Sleep data ",abs(awakecount - sleepcount))
                        totalloss = totalloss + abs(awakecount - sleepcount)
                    if tmpacount > tmpccount:
                        if abs(awakecount - tmpacount) > 0:
                            totalloss = totalloss + abs(awakecount - tmpacount)
                            print("Missed Wake-TempA data ",abs(awakecount - tmpacount))
                        if abs(sleepcount - tmpacount) > 0:
                            totalloss = totalloss + abs(sleepcount - tmpacount)
                            print("Missed Sleep-TempA data ",abs(sleepcount - tmpacount))
                    else:
                        if abs(sleepcount - tmpccount) > 0:
                            totalloss = totalloss + abs(sleepcount - tmpccount)
                            print("Missed Sleep-TempC data ",abs(sleepcount - tmpccount))
                        if abs(awakecount - tmpccount) > 0:
                            totalloss = totalloss + abs(awakecount - tmpccount)
                            print("Missed Wake-TempC data ",abs(awakecount - tmpccount))
                    subcycle +=1
                cycle += 1

                print("---------------------------------------")
                print("Total Loss Count is: ",totalloss)
                print("---------------------------------------------------------")

        if rflib.event.is_set():
            break
  except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        print("Exception type: ", exception_type)
        print("Line number: ", line_number)
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        rflib.event.set()
        exit()

def main():
  print ("JemRF Serial Test Monitor 2.3.0")
  print ("Press ctrl-c to exit")

  rflib.init()
  #start serial processing thread
  a=Thread(target=rf2serial, args=())
  a.start()

  request = request_reply("a01HELLO")
  if (request.rt==1):
      for x in range(request.num_replies):
        print(str(request.id[x]) + str(request.message[x]))

  #now start processing thread
  b=Thread(target=inbound_message_processing, args=())
  b.start()

  while not rflib.event.is_set():
      try:
          sleep(1)
      except KeyboardInterrupt:
          rflib.event.set()
          break
  print("End of Event")
  print(rflib.event.is_set())

if __name__ == "__main__":
    try:
      main()
    except Exception as e:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      message += exe_tb.tb_lineno
      print (message)
      print (e)
      rflib.event.set()
    finally:
      rflib.event.set()
      exit()

