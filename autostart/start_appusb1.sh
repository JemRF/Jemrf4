#!/bin/bash

lxterminal --title="USB1" --geometry=80x48  --command="/home/pi/autostart/appusb1.sh" &
# Wait until window appears
until wmctrl -l | grep -q "USB1"; do
  sleep 0.2
done

# Extra delay for WM to finish layout
sleep 2.5
wmctrl -r "USB1" -e 0,900,50,-1,-1

