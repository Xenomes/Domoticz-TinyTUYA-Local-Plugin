# Domoticz-TinyTUYA-Local-Plugin
TUYA Plugin for Domoticz home automation

Controls TUYA devices on your local network mainly on/off in the future maybe more devices.

## Installation

The plugin make use of the project Tinytuya there for is a IoT Cloud Platform account needed, for setup up see https://github.com/jasonacox/tinytuya step 3 or see PDF https://github.com/jasonacox/tinytuya/files/8145832/Tuya.IoT.API.Setup.pdf

Python version 3.8 or higher required & Domoticz version 2022.2 or greater.

To install:
* Go in your Domoticz directory using a command line and open the plugins directory.
* ```cd ~/domoticz/plugins``` for most user or go to the Docker volume mount plugins directory.
* The plugin required Python library tinytuya ```sudo pip3 install requests==2.23.0 charset-normalizer==3.0.1 tinytuya -U```
* Run: ```git clone https://github.com/Xenomes/Domoticz-TinyTUYA-Local-Plugin.git```
* Run ```python3 -m tinytuya wizard``` fill in the credentials from the IoT Cloud account, say 'Yes' to the following cuestions. A deviceID can be found on your IOT account of Tuya got to Cloud => your project => Devices => Pick one of you device ID.
* Restart Domoticz.

## Updating

To update:
* Upgrade the tinytuya library ```sudo pip3 install tinytuya -U```
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-TinyTUYA-Plugin directory.
* ```cd ~/domoticz/plugins/Domoticz-TinyTUYA-Local-Plugin``` for most user or go to the Docker volume mount plugins/Domoticz-TinyTUYA-Plugin directory.
* Run: ```git pull```
* Restart Domoticz.

## Subscription expired
Is your subscription to cloud development plan expired, you can extend it <a href="https://iot.tuya.com/cloud/products/apply-extension"> HERE</a><br/>

## Configuration

There is no extra information need, the info is readout of file 'devices.json' located in the plugin folder, keep the setting 'Data Timeout' at the plug-in disabled.
For the best performed it is advised to give the tuya devices a static ip, see your router manufacturer manual to setup static ip's.

## Usage

In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "TinyTUYATinyTUYA (Local Control)" add the hardware.

## Test device

I had only a RGBWW light to fully test the script, if there is a device missing in the plugin you can provide the json file by create a post in issues on Github.

## Change log

| Version | Information|
| --- | ---------- |
| 0.1 | Initial upload version |

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/xenomes)