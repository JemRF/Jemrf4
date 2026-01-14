#!/bin/bash
cd /home/pi/Jemrf4/
trap "echo 'Exiting...'; exit 0" SIGINT SIGTERM
while true; do
    ./serial_mon.py
    echo "serial_mon.py exited. Restarting in 2 seconds..."
    sleep 2
done
exec bash
