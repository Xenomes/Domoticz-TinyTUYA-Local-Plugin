# Domoticz TinyTUYA Local Plugin
#
# Author: Xenomes (xenomes@outlook.com)
#
"""
<plugin key="tinytuyalocal" name="TinyTUYA (Local Control)" author="Xenomes" version="0.1" wikilink="" externallink="https://github.com/Xenomes/Domoticz-TinyTUYA-Local-Plugin.git">
    <description>
        <h2>TinyTUYA Plugin Local Controlversion Alpha 0.1</h2><br/>
        <br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>On/Off control</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>All devices that have on/off state should be supported</li>
        </ul>
    </description>
    <params>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic + Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections + Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
try:
    import DomoticzEx as Domoticz
except ImportError:
    import fakeDomoticz as Domoticz
import tinytuya
# from tinytuya import Contrib
import subprocess
import platform
import sys
import json
import time

class BasePlugin:
    enabled = False
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log('TinyTUYA ' + Parameters['Version'] + ' plugin started')
        Domoticz.Log('TinyTuyaVersion:' + tinytuya.version )
        if Parameters['Mode6'] != '0':
            Domoticz.Debugging(int(Parameters['Mode6']))
            # Domoticz.Log('Debugger started, use 'telnet 0.0.0.0 4444' to connect')
            # import rpdb
            # rpdb.set_trace()
            DumpConfigToLog()
        Domoticz.Heartbeat(10)
        onHandleThread(True)

    def onStop(self):
        Domoticz.Log('onStop called')

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log('onConnect called')

    def onMessage(self, Connection, Data):
        Domoticz.Log('onMessage called')

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Debug("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + "', Color: " + str(Color))

        # device for the Domoticz
        dev = Devices[DeviceID].Units[Unit]
        Domoticz.Debug('Device ID: ' + str(DeviceID))

        Domoticz.Debug('nValue: ' + str(dev.nValue))
        Domoticz.Debug('sValue: ' + str(dev.sValue) + ' Type ' + str(type(dev.sValue)))
        Domoticz.Debug('LastLevel: ' + str(dev.LastLevel))

        # Control device and update status in Domoticz
        if Command == 'Off':
            SendCommand(DeviceID, 'switch', False)
            UpdateDevice(DeviceID, Unit, 'Off', 0, 0)
        elif Command == 'On':
            SendCommand(DeviceID, 'switch', True)
            UpdateDevice(DeviceID, Unit, 'On', 1, 0)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log('Notification: ' + Name + ', ' + Subject + ', ' + Text + ', ' + Status + ', ' + str(Priority) + ', ' + Sound + ', ' + ImageFile)

    def onDeviceRemoved(self, DeviceID, Unit):
        Domoticz.Log('onDeviceDeleted called')

    def onDisconnect(self, Connection):
        Domoticz.Log('onDisconnect called')

    def onHeartbeat(self):
        Domoticz.Debug('onHeartbeat called')
        # if time.time() - last_update < 60:
        #     Domoticz.Debug("onHeartbeat called skipped")
        #     return
        Domoticz.Debug("onHeartbeat called last run: " + str(time.time() - last_update))
        onHandleThread(False)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onHandleThread(startup):
    # Run for every device on startup and heartbeat
    try:
        if startup == True:
            global tuya
            global devs
            global last_update
            last_update = time.time()
            devs = None
            with open(Parameters['HomeFolder'] + '/devices.json') as dFile:
                devs = json.load(dFile)

        # Initialize/Update devices from TUYA API
        if devs is None:
            Domoticz.Error('devices.json is missing in the plugin folder!')
            return
        for dev in devs:
            Domoticz.Debug( 'Device name=' + str(dev['name']) + ' id=' + str(dev['id']) + ' ip=' + str(dev['ip']) + ' key=' + str(dev['key']) + ' version=' + str(dev['version']))
            # Create devices
            if str(dev['ip']) != '':
                tuya = tinytuya.Device(str(dev['id']), str(dev['ip']), str(dev['key']))
                # tuya.use_old_device_list = True
                # tuya.new_sign_algorithm = True
                tuya.set_version(float(dev['version']))

                if startup == True:
                    Domoticz.Debug('Run Startup script')
                    if  createDevice(dev['id'], 1) :
                        Domoticz.Log('Create device Switch')
                        Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=1, Type=244, Subtype=73, Switchtype=0, Image=9, Used=1).Create()

                    setConfigItem(dev['id'], {'key': dev['key'], 'ip': dev['ip'], 'version': dev['version']})

                #update devices in Domoticz
                Domoticz.Log('Update devices in Domoticz')
                # status Domoticz
                # sValue = Devices[dev['id']].Units[1].sValue
                # nValue = Devices[dev['id']].Units[1].nValue
                # Domoticz.Debug(tuya.status())
                currentstatus = tuya.status()['dps']['1']
                if bool(currentstatus) == False:
                    UpdateDevice(dev['id'], 1, 'Off', 0, 0)
                elif bool(currentstatus) == True:
                    UpdateDevice(dev['id'], 1, 'On', 1, 0)

    except Exception as err:
        Domoticz.Error('handleThread: ' + str(err))
        Domoticz.Debug('handleThread: ' + str(err)  + ' line ' + format(sys.exc_info()[-1].tb_lineno))

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("--->Unit Count:      '" + str(len(Device.Units)) + "'")
        for UnitNo in Device.Units:
            Unit = Device.Units[UnitNo]
            Domoticz.Debug("--->Unit:           " + str(UnitNo))
            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
    return

def UpdateDevice(ID, Unit, sValue, nValue, TimedOut, AlwaysUpdate = 0):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if str(Devices[ID].Units[Unit].sValue) != str(sValue) or str(Devices[ID].Units[Unit].nValue) != str(nValue) or str(Devices[ID].TimedOut) != str(TimedOut) or AlwaysUpdate == 1:
        if sValue == None:
            sValue = Devices[ID].Units[Unit].sValue
        Devices[ID].Units[Unit].sValue = str(sValue)
        if type(sValue) == int or type(sValue) == float:
            Devices[ID].Units[Unit].LastLevel = sValue
        elif type(sValue) == dict:
            Devices[ID].Units[Unit].Color = json.dumps(sValue)
        Devices[ID].Units[Unit].nValue = nValue
        Devices[ID].TimedOut = TimedOut
        Devices[ID].Units[Unit].Update(Log=True)

        Domoticz.Debug('Update device value: ' + str(ID) + ' Unit: ' + str(Unit) + ' sValue: ' +  str(sValue) + ' nValue: ' + str(nValue) + ' TimedOut=' + str(TimedOut))
    return

def SendCommand(ID, CommandName, Status):
    Domoticz.Debug(str(getConfigItem(ID,'id')) + ' ' + str(getConfigItem(ID,'ip'))  + ' ' +  str(getConfigItem(ID,'key')))
    tuya = tinytuya.Device(str(ID), getConfigItem(ID,'ip'), getConfigItem(ID,'key'))
    tuya.set_version(float(getConfigItem(ID,'version')))
    if Status == True:
        tuya.turn_on()
    elif Status == False:
        tuya.turn_off()
    else:
        Domoticz.Debug('Unknown Command')
    Domoticz.Debug('Command send to tuya :' + str(ID) + ", " + str({'commands': [{'code': CommandName, 'value': Status}]}))

def createDevice(ID, Unit):
    if ID in Devices:
        if Unit in Devices[ID].Units:
            value = False
        else:
            value = True
    else:
        value = True

    return value

def ping_ok(sHost) -> bool:
    try:
        subprocess.check_output(
            "ping -{} 1 {}".format("n" if platform.system().lower() == "windows" else "c", sHost), shell=True
        )
    except Exception:
        return False

    return True

# Configuration Helpers
def getConfigItem(Key=None, Values=None):
    Value = {}
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            # Domoticz.Debug(Config[Key][Values])
            Value = Config[Key][Values]  # only return requested key if there was one
        else:
            Value = Config      # return the whole configuration if no key
    except KeyError:
        Value = {}
    except Exception as inst:
        Domoticz.Error('Domoticz.Configuration read failed: ' + str(inst))
    return Value

def setConfigItem(Key=None, Value=None):
    Config = {}
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Config[Key] = Value
        else:
            Config = Value  # set whole configuration if no key specified
        Config = Domoticz.Configuration(Config)
    except Exception as inst:
        Domoticz.Error('Domoticz.Configuration operation failed: ' + str(inst))
    return Config

def version(v):
    return tuple(map(int, (v.split("."))))