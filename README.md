# NOT YET READY FOR LIVE SYSTEMS



# Domoticz-TinyTUYA-Local-Plugin
TUYA Plugin for Domoticz home automation

Controls TUYA devices on your local network.

## Installation

The plugin make use of the project Tinytuya there for is a IoT Cloud Platform account needed, for setup up see https://github.com/jasonacox/tinytuya step 3 or see PDF https://github.com/jasonacox/tinytuya/files/12836816/Tuya.IoT.API.Setup.v2.pdf
for the best compatibility, set your devices to 'DP instruction' in the device settings under iot.tuya.com.

Python version 3.8 or higher required & Domoticz version 2024.1 or greater.

To install:
* Go in your Domoticz directory using a command line and open the plugins directory.
* ```cd ~/domoticz/plugins``` for most user or go to the Docker volume mount plugins directory.
* The plugin required Python library tinytuya ```sudo pip3 install requests==2.23.0 charset-normalizer==3.0.1 tinytuya -U```
* Run: ```git clone https://github.com/Xenomes/Domoticz-TinyTUYA-Local-Plugin.git```
* Run ```python3 -m tinytuya wizard``` fill in the credentials from the IoT Cloud account, say 'Yes' to the following questions. A deviceID can be found on your IOT account of Tuya got to Cloud => your project => Devices => Pick one of you device ID. (Keep a copy of 'devices.json' for the furtur)
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

In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "TinyTUYA (Local Control)" add the hardware.

## Test device

I only had an RGBWW light to fully test the script. If there is a device missing in the plugin, you can provide the JSON file by creating a post in issues on GitHub. Don't forget to obfuscate the 'Key' in the JSON.

## Change log

| Version | Information|
| --- | ---------- |
| 0.1 | Initial upload version |
| 0.2 | Add unit detection devices |
| 0.3 | Add True and False statment |

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/xenomes)