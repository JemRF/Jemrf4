#!/bin/bash

lxterminal --title="USB2" --geometry=80x48 --command="/home/pi/autostart/appusb2.sh" &
# Wait until window appears
until wmctrl -l | grep -q "USB2"; do
  sleep 0.2
done

# Extra delay for WM to finish layout
sleep 3.5
wmctrl -r "USB2" -e 0,1350,50,-1,-1

