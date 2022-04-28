#!/bin/bash

# install alexa dependencies
apt install libcurl4-openssl-dev gstreamer1.0-alsa gstreamer1.0-tools gstreamer1.0-plugins-ugly

#download alexa stuff info
wget https://raw.githubusercontent.com/alexa/avs-device-sdk/master/tools/Install/setup.sh 
wget https://raw.githubusercontent.com/alexa/avs-device-sdk/master/tools/Install/genConfig.sh
wget https://raw.githubusercontent.com/alexa/avs-device-sdk/master/tools/Install/pi.sh

