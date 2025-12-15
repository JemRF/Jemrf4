#!/usr/bin/env python
# Updated to python 3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from serial_mon import *

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
      exit()#include ../serial_mon


