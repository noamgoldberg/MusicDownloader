#!/bin/bash
# setup.sh - Install necessary system packages for Streamlit app

# Update package list and install common utilities
sudo apt-get update
sudo apt-get install -y wget curl unzip

# Install required libraries for Chromium
sudo apt-get install -y libx11-dev libx11-xcb1 libxcomposite1 libxdamage1 libxi6 libgdk-pixbuf2.0-0 libnss3 libxtst6 libatk-bridge2.0-0 libgtk-3-0 libdbus-1-3
sudo apt-get install -y libgbm1 libasound2 libxrandr2 libu2f-udev
sudo apt-get install -y libglib2.0-0=2.50.3-2 \
    libnss3=2:3.26.2-1.1+deb9u1 \
    libgconf-2-4=3.2.6-4+b1 \
    libfontconfig1=2.11.0-6.7+b1