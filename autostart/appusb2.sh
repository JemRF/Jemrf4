cd /home/pi/Jemrf4/usb2
while true; do
    ./serial_mon.py
    echo "serial_mon.py exited. Restarting in 2 seconds..."
    sleep 2
done
exec bash

