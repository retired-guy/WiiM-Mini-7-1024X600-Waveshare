# WiiM-Mini-7-1024X600-Waveshare
Display for WiiM Mini using Waveshare 7" 1024x600 IPS display and Raspberry Pi Zero W (or Zero 2W)

![photo](https://raw.githubusercontent.com/retired-guy/WiiM-Mini-7-1024X600-Waveshare/main/US6zwYgZTTeb24smzn9lBQ.jpeg)

Installation notes

NOTE!!!!!!!

Was unable to get the waveshare to work on Bullseye.  These instructions are strictly for Raspberry Pi OS-Lite Buster on a Raspberry Pi Zero (original)

!!!!!!!!!!!

Create a micro-SD card with the Raspberry Pi OS-Lite Buster distro using the instructions on the RPi site

With the SD card still on your computer:

Waveshare Wiki https://www.waveshare.com/wiki/7inch_LCD_for_Pi

edit /boot/config.txt on the SD card per the Wiki for Buster

For WiFi network login, set up wpa_supplicant.conf, and save to the /boot direcory on the SD card

https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-networking31

To enable ssh login, create a blank file named simply ssh (NOT ssh.txt), and save it to the /boot directory on the SD card

Eject the SD card and put it in the Pi Zero

Power up the Pi

ssh in as pi/raspberry (using ssh or putty) 

the screen should display the ip address of the Pi

ssh pi@192.168.68.xxx

raspberry

follow instruction to change default password, then

sudo apt update

sudo apt upgrade

Install pip, then Pillow and its dependencies:

https://pillow.readthedocs.io/en/stable/installation.html

sudo apt install python3-pip

sudo python3 -m pip install --upgrade pip

sudo apt install libopenjp2-7-dev

sudo apt install libtiff5

sudo python3 -m pip install --upgrade Pillow

Make sure pi user has access to the screen

sudo usermod -a -G video pi

Download, unzip and rename the script

cd

wget https://github.com/retired-guy/WiiM-Mini-7-1024X600-Waveshare/archive/refs/heads/main.zip

unzip main.zip

mv WiiM-Mini-7-1024X600-Waveshare-main wiim

cd wiim

Set up the wiim service, so it loads at bootup

sudo mv wiim.service /etc/systemd/system/wiim.service

sudo systemctl enable wiim.service

chmod +x wiim.py

Install wiim app dependencies

sudo python3 -m pip install async-upnp-client

sudo python3 -m pip install xmltodict

sudo apt install fonts-dejavu

cd /usr/share/fonts/truetype

sudo mkdir oswald

cd oswald

sudo wget -O oswald.zip https://www.fontsquirrel.com/fonts/download/oswald

sudo unzip oswald.zip

cd ~/wiim

./wiim.py

If working, ^C out of wiim.py, sudo reboot, and it should boot into the WiiM monitor app


