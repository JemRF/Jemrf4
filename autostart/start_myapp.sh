#!/bin/bash

lxterminal --title="Channel 0" --geometry=80x48  --command="/home/pi/autostart/app1.sh" &

# Wait until window appears
until wmctrl -l | grep -q "Channel 0"; do
  sleep 0.2
done

# Extra delay for WM to finish layout
sleep 0.5
wmctrl -r "Channel 0" -e 0,0,50,-1,-1

