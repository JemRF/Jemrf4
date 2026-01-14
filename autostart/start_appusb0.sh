#!/bin/bash

lxterminal --title="USB0" --geometry=80x48  --command="/home/pi/autostart/appusb0.sh" &
# Wait until window appears
until wmctrl -l | grep -q "USB0"; do
  sleep 0.2
done

# Extra delay for WM to finish layout
sleep 1.5
wmctrl -r "USB0" -e 0,450,50,-1,-1

