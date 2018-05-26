#!/bin/bash

virtualenv venv
. venv/Scripts/activate

pip install requests selenium beautifulsoup4 dotmap

PLATFORM=win32
VERSION=$(curl http://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl http://chromedriver.storage.googleapis.com/$VERSION/chromedriver_$PLATFORM.zip --output chromedriver.zip
unzip chromedriver.zip -d venv/Scripts/
rm chromedriver.zip

# Needed for fetch script to work with all MSys2 bashs (e.g git bash)
# alias python='winpty python.exe'
# echo "alias python='winpty python.exe'" >> ~/.bashrc
