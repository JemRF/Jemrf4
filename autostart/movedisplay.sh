#!/bin/bash
lxterminal --title="App 2" --geometry=80x24 &
sleep 0.5
wmctrl -r "App 2" -e 0,1250,30,48,80

