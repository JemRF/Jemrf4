To setup apps for autostart

sudo apt install wmctrl -y

Copy config apps for all the apps you want auto-started
1. copy config apps to ~/.config/autostart    (~/.config/autostart folder may need to be created)
2. copy autostart app to ~/autostart    (~/autostart folder may need to be created)

System on boot will run the apps in the ~/.config/autostart folder 
The autostart apps point to the apps in the ~/autostart folder

NOTE: may need to change home folder from /home/pi to user name
to change pi to glenn, run this in both autostart folders:
sed -i 's|/pi/|/glenn/|g' *

