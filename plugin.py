# Domoticz TinyTUYA Local Plugin
#
# Author: Xenomes (xenomes@outlook.com)
#
"""
<plugin key="tinytuyalocal" name="TinyTUYA (Local Control)" author="Xenomes" version="0.2" wikilink="" externallink="https://github.com/Xenomes/Domoticz-TinyTUYA-Local-Plugin.git">
    <description>
        <h2>TinyTUYA Plugin Local Controlversion Alpha 0.2</h2><br/>
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
import ast
import time
import base64

class BasePlugin:
    enabled = False
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log('TinyTUYA ' + Parameters['Version'] + ' plugin started')
        Domoticz.Log('TinyTuya Version:' + tinytuya.version )
        if Parameters['Mode6'] != '0':
            Domoticz.Debugging(int(Parameters['Mode6']))
            # Domoticz.Log('Debugger started, use 'telnet 0.0.0.0 4444' to connect')
            # import rpdb
            # rpdb.set_trace()
            DumpConfigToLog()
        # Domoticz.Heartbeat(10)
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
        category = getConfigItem(DeviceID, 'category')
        # Domoticz.Debug('Device ID: ' + str(DeviceID))
        # Domoticz.Debug('Category: ' + str(category))
        # Domoticz.Debug('nValue: ' + str(dev.nValue))
        # Domoticz.Debug('sValue: ' + str(dev.sValue) + ' Type ' + str(type(dev.sValue)))
        # Domoticz.Debug('LastLevel: ' + str(dev.LastLevel))

        # Control device and update status in Domoticz
        if Command == 'Set Level':
            SendCommand(DeviceID, Unit, Level, category)
            UpdateDevice(DeviceID, Unit, Level, 1, 0)
        elif Command == 'Set Color':
            SendCommand(DeviceID, Unit, eval(Color), category)
            UpdateDevice(DeviceID, Unit, Color, 1, 0)
        else:
            SendCommand(DeviceID, Unit, True if Command not in  ['Off', 'Close'] else False, category)
            UpdateDevice(DeviceID, Unit, Command, 1 if Command not in  ['Off', 'Close'] else 0, 0)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log('Notification: ' + Name + ', ' + Subject + ', ' + Text + ', ' + Status + ', ' + str(Priority) + ', ' + Sound + ', ' + ImageFile)

    def onDeviceRemoved(self, DeviceID, Unit):
        Domoticz.Log('onDeviceDeleted called')

    def onDisconnect(self, Connection):
        Domoticz.Log('onDisconnect called')

    def onHeartbeat(self):
        Domoticz.Debug('onHeartbeat called')
        # if time.time() - getConfigItem(DeviceID, 'last_update') < 10:
        #     Domoticz.Debug("onHeartbeat called skipped")
        #     return
        # Domoticz.Debug("onHeartbeat called last run: " + str(time.time() - last_update))
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
            exit
        # Create devices
        for dev in devs:
            Domoticz.Debug( 'Device name=' + str(dev['name']) + ' id=' + str(dev['id']) + ' ip=' + str(dev['ip']) + ' version=' + str(dev['version'])) # ' key=' + str(dev['key']) +
            mapping = dev['mapping']
            dev_type = DeviceType(dev['category'])
            for key, value in mapping.items():
                value['dp'] = key
            code_list = [value['code'] for key, value in mapping.items()]
            # Domoticz.Debug(str(code_list))
            if str(dev['ip']) != '':
                # tuya = tinytuya.Device(ev_id=str(dev['id']), address=str(dev['ip']), local_key=str(dev['key']), version=float(dev['version']))
                # tuya.use_old_device_list = True
                # tuya.new_sign_algorithm = True

                if startup == True:
                    Domoticz.Debug('Run Startup script')
                    if dev_type in ('light', 'fanlight', 'pirlight'):
                        unit = 1
                        if createDevice(dev['id'], unit):
                            # Domoticz.Debug('Code List: ' + str(code_list))
                            # Create Lights
                            if ('switch_led' in code_list or 'led_switch' in code_list or 'switch_led_1' in code_list or 'switch_led_2' in code_list) and 'work_mode' in code_list and ('colour_data' in code_list or 'colour_data_v2' in code_list) and ('temp_value' in code_list or 'temp_value_v2' in code_list) and ('bright_value' in code_list or 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light RGBWW')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=241, Subtype=4, Switchtype=7, Used=1).Create() #RGBWW
                            elif ('switch_led' in code_list or 'led_switch' in code_list or 'switch_led_1' in code_list or 'switch_led_2' in code_list) and 'work_mode' in code_list and ('colour_data' in code_list or 'colour_data_v2' in code_list) and ('temp_value' in code_list or 'temp_value_v2' in code_list) and not('bright_value' in code_list and 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light RGBW')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=241, Subtype=1, Switchtype=7, Used=1).Create() #RGBW
                            elif ('switch_led' in code_list or 'led_switch' in code_list) and not ('work_mode' in code_list) and ('colour_data' in code_list or 'colour_data_v2' in code_list) and not('temp_value' in code_list and 'temp_value_v2' in code_list) and ('bright_value' in code_list or 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light RGB')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=241, Subtype=2, Switchtype=7, Used=1).Create() #RGB
                            elif ('switch_led' in code_list or 'led_switch' in code_list) and 'work_mode' in code_list and not ('colour_data' in code_list and 'colour_data_v2' in code_list) and ('temp_value' in code_list or 'temp_value_v2' in code_list) and ('bright_value' in code_list or 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light WWCW')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=241, Subtype=8, Switchtype=7, Used=1).Create() #Cold white + Warm white
                            elif ('switch_led' in code_list or 'led_switch' in code_list) and not ('work_mode' in code_list) and not ('colour_data' in code_list and 'colour_data_v2' in code_list) and not ('temp_value' in code_list and 'temp_value_v2' in code_list) and ('bright_value' in code_list or 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light Dimmer')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=241, Subtype=3, Switchtype=7, Used=1).Create() #White
                            elif ('switch_led' in code_list or 'led_switch' in code_list) and not ('work_mode' in code_list) and not ('colour_data' in code_list and 'colour_data_v2' in code_list) and not ('temp_value' in code_list and 'temp_value_v2' in code_list) and not('bright_value' in code_list and 'bright_value_v2' in code_list):
                                Domoticz.Log('Create device Light On/Off')
                                Domoticz.Unit(Name=dev['name'], DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=7, Used=1).Create() #Dimmer
                            else:
                                Domoticz.Log('Create device Light On/Off (Unknown Light Device)')
                                Domoticz.Unit(Name=dev['name'] + ' (Unknown Light Device)', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=0, Used=1).Create() #On/Off
                    elif dev_type not in ('light', 'fanlight', 'pirlight'):
                        for item in mapping.values():
                            # Domoticz.Debug(str(item['code']))
                            unit = int(item['dp'])
                            if  createDevice(dev['id'], unit):

                                # Create Switch
                                if item['code'] in [f'switch{i}' for i in range(1, 9)] + [f'switch_{i}' for i in range(1, 9)] + ['switch', 'fan_switch', 'window_check', 'child_lock', 'muffling', 'light', 'colour_switch', 'anion', 'switch_charge', 'laser_switch', 'doorcontact', 'doorcontact_state', 'door_control_1', 'door_state_1', 'smartlock', 'position', 'switch_pir', 'fan_speed']:
                                    Domoticz.Log('Create device Switch')
                                    if item['code'] in ['doorcontact', 'doorcontact_state', 'door_control_1', 'door_state_1', 'smartlock']:
                                        Domoticz.Log('Create Doorcontact device')
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=11, Used=1).Create() #Contact
                                    elif item['code'] in ['position']:
                                        Domoticz.Log('Create Cover device')
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=21, Used=1).Create() #Blinds Percentage With Stop
                                    elif item['code'] in ['switch_pir']:
                                        Domoticz.Log('Create Motion Sensor device')
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=8, Used=1).Create() #Motion Sensor
                                    elif item['code'] in ['laser_bright',  'fan_speed']:
                                        Domoticz.Log('Create Dimmer device')
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=7, Used=1).Create() #Dimmer
                                    else:
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=73, Switchtype=0, Used=1).Create() #On/Off

                                # Create Selection Switch
                                elif item['code'] in ['mode', 'work_mode', 'speed', 'fan_direction', 'Alarmtype', 'AlarmPeriod', 'alarm_state', 'status', 'alarm_volume', 'alarm_lock', 'cistern', 'fault', 'suction', 'cistern', 'fan_speed_enum', 'dehumidify_set_value', 'device_mode', 'pir_sensitivity', 'manual_feed', 'manual_feed', 'feed_state', 'feed_report', 'alarm_lock', 'switch_mode', 'laser_switch'] + [f'switch{i}_value' for i in range(1, 9)] + [f'switch_type_{i}' for i in range(1, 9)]:
                                    Domoticz.Log('Create Selection device')
                                    if item['code'] == 'mode':
                                        the_values = item['values']
                                        mode = ['off']
                                        mode.extend(the_values.get('range'))
                                        options = {}
                                        options['LevelOffHidden'] = 'true'
                                        options['LevelActions'] = ''
                                        options['LevelNames'] = '|'.join(mode)
                                        options['SelectorStyle'] = '0' if len(mode) < 5 else '1'
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=options, Image=9, Used=1).Create() #Selector Switch

                                # Powermetering
                                elif item['code'] in ['ActivePowerA'] in code_list and ['ActivePowerB'] in code_list and ['ActivePowerC']:
                                    Domoticz.Log('Create Current (3 Phase) device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=89, Subtype=1, Used=1).Create() #Ampere (3 Phase)
                                elif item['code'] in ['cur_power', 'cur_power', 'power_a', 'power_b']:
                                    Domoticz.Log('Create Watt device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=248, Subtype=1, Switchtype=0, Used=1).Create() #Electric Usage
                                elif item['code'] in ['cur_current', 'cmp_cur', 'leakage_current', 'Current']:
                                    Domoticz.Log('Create Amperes device')
                                    the_values = item['values']
                                    if the_values.get('unit') != 'A':
                                        options = {}
                                        options['Custom'] = '1;'+ the_values.get('unit')
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=31, Switchtype=0, Used=1).Create() #Custom Sensor
                                    else:
                                        Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=23, Switchtype=0, Used=1).Create() #Current (Single)
                                elif item['code'] in ['voltage_a', 'cur_voltage', 'cur_voltage']:
                                    Domoticz.Log('Create Volt device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=8, Switchtype=0, Used=1).Create() #Voltage
                                elif item['code'] in ['cur_power', 'ActivePower', 'ActivePowerA', 'ActivePowerB', 'ActivePowerC', 'phase_a', 'total_power', 'cur_power']:
                                    Domoticz.Log('Create Power device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=29, Used=1).Create() #kWh
                                elif item['code'] in ['phase_a'] and item['type'] in ['Raw']:
                                    Domoticz.Unit(Name=dev['name'] + ' (A)', DeviceID=dev['id'], Unit=100 + unit, Type=243, Subtype=23, Used=1).Create()
                                    Domoticz.Unit(Name=dev['name'] + ' (W)', DeviceID=dev['id'], Unit=101 + unit, Type=248, Subtype=1, Used=1).Create()
                                    Domoticz.Unit(Name=dev['name'] + ' (V)', DeviceID=dev['id'], Unit=102 + unit, Type=243, Subtype=8, Used=1).Create()
                                    Domoticz.Unit(Name=dev['name'] + ' (kWh)', DeviceID=dev['id'],Unit=103 + unit, Type=243, Subtype=29, Used=1).Create()

                                # Create Sensors
                                elif item['code'] in ['temp_current', 'intemp', 'outtemp', 'whjtemp', 'cmptemp', 'wttemp', 'hqtemp', 'va_temperature''sub1_temp', 'sub2_temp', 'sub3_temp', 'Temperature', 'temp_indoor', 'temperature']:
                                    Domoticz.Log('Create Temperature device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=80, Subtype=5, Used=1).Create() #Temperature sensor
                                elif item['code'] in ['va_humidity', 'sub1_hum', 'sub2_hum', 'sub3_hum', 'humidity_indoor']:
                                    Domoticz.Log('Create Humidity device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=81, Subtype=1, Used=1).Create() #Humidity sensor
                                elif item['code'] in ['electricity_left', 'filter']:
                                    Domoticz.Log('Create Percentage device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=6, Used=1).Create() #Percentage
                                elif item['code'] in ['bright_value']:
                                    Domoticz.Log('Create Lux device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=246, Subtype=1, Switchtype=11, Used=1).Create() #Lux
                                elif item['code'] in ['co2_value']:
                                    Domoticz.Log('Create Custom device')
                                    the_values = item['values']
                                    options = {}
                                    options['Custom'] = the_values.get('unit')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=31, Options=options, Used=1).Create() #Custom Sensor
                                elif item['code'] in ['air_quality_index', 'direction_a', 'direction_b', 'gateway', 'status', 'fault', 'multifunctionalarm', 'air_quality', 'watersensor_state']:
                                    Domoticz.Log('Create Text device')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=19, Image=13, Used=1).Create() #Text

                                # Create SetPoint device
                                elif item['code'] in ['set_temp', 'temp_set', 'cook_temperature', 'wth_stemp', 'ach_stemp', 'aircond_temp_diff', 'wth_temp_diff', 'acc_stemp']:
                                    the_values = item['values']
                                    options = {}
                                    options['ValueStep'] = the_values.get('step')
                                    options['ValueMin'] = the_values.get('min')
                                    options['ValueMax'] = the_values.get('max')
                                    options['ValueUnit'] = the_values.get('unit')
                                    Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=242, Subtype=1, Options=options, Used=1).Create() #Set Point

                                # elif dev_type == 'infrared':
                                #     Domoticz.Unit(Name=dev['name'] + ' (' + str(item['code']) + ')', DeviceID=dev['id'], Unit=unit, Type=243, Subtype=19, Used=0).Create()
                                #     UpdateDevice(dev['id'], unit, 'Infrared devices are not yet able to be controlled by the plugin.', 0, 0)
                                else:
                                    Domoticz.Debug('No mapping found for device: ' + str(dev['name']) + ' sub device: ' + str(item['code']))

                    setConfigItem(dev['id'], {'unit': unit, 'category': dev_type, 'key': dev['key'], 'ip': dev['ip'], 'version': dev['version'], 'last_update': 0})

                else:
                    # update devices inDomoticz
                    Domoticz.Debug('Update devices in Domoticz')
                    # status Domoticz
                    # sValue = Devices[dev['id']].Units[1].sValue
                    # nValue = Devices[dev['id']].Units[1].nValue
                    # Domoticz.Debug(tuya.status())
                    tuya = tinytuya.Device(dev_id=str(dev['id']), address=str(dev['ip']), local_key=str(dev['key']), version=str(dev['version']), connection_timeout=1, connection_retry_limit=1)
                    tuya.detect_available_dps()
                    if time.time() > float(getConfigItem(dev['id'], 'last_update')):
                        tuyastatus = tuya.status()
                        # Domoticz.Debug('tuyastatus: ' + str(tuyastatus))
                        if 'Device Unreachable' in str(tuyastatus):
                            Domoticz.Error('Device :' + dev['id'] + ' is Offline!')
                            setConfigItem(dev['id'], {'last_update': time.time() + 300})
                            UpdateDevice(dev['id'], 1, 'Off', 0, 1)
                        else:
                            # Domoticz.Debug('Type: ' + str(dev_type))
                            if dev_type in ('light', 'fanlight', 'pirlight'):
                                unit = 1
                                UpdateDevice(dev['id'], unit, True if bool(tuyastatus['dps']['1']) == True else False, 0 if bool(tuyastatus['dps']['1']) == False else 1, 0)
                            if dev_type not in ('light', 'pirlight'):
                                # Domoticz.Debug(str(mapping.values()))
                                for item in mapping.values():
                                    # Create sub devices
                                    try:
                                        unit = int(item['dp'])
                                        currentstatus = convert_to_correct_type(tuyastatus['dps'][str(unit)])
                                        # Domoticz.Debug('Unit: ' + str(unit))
                                        # Domoticz.Debug(str(item['code']))
                                        # Domoticz.Debug('Currentstatus: ' + str(currentstatus))
                                        # Create Switch
                                        if item['code'] in ('switch', 'switch_1', 'switch_2'):
                                            UpdateDevice(dev['id'], unit, currentstatus, 0 if currentstatus == False else 1, 0)
                                        elif item['code'] in ['phase_a'] and item['type'] in ['Raw']:
                                            decoded_data = base64.b64decode(currentstatus)
                                            # Extract voltage, current, and power data
                                            currentvoltage = int.from_bytes(decoded_data[:2], byteorder='big') * 0.1
                                            currentcurrent = int.from_bytes(decoded_data[2:5], byteorder='big') * 0.001
                                            currentpower = int.from_bytes(decoded_data[5:8], byteorder='big')
                                            UpdateDevice(dev['id'], 100 + unit, str(currentcurrent), 0, 0)
                                            UpdateDevice(dev['id'], 101 + unit, str(currentpower), 0, 0)
                                            UpdateDevice(dev['id'], 102 + unit, str(currentvoltage), 0, 0)
                                            lastupdate = (int(time.time()) - int(time.mktime(time.strptime(Devices[dev['id']].Units[103 + unit].LastUpdate, '%Y-%m-%d %H:%M:%S'))))
                                            lastvalue = Devices[dev['id']].Units[103 + unit].sValue if len(Devices[dev['id']].Units[103 + unit].sValue) > 0 else '0;0'
                                            UpdateDevice(dev['id'], 103 + unit, str(currentpower) + ';' + str(float(lastvalue.split(';')[1]) + ((currentpower) * (lastupdate / 3600))) , 0, 0, 1)
                                        else:
                                            UpdateDevice(dev['id'], unit, str(currentstatus), 0 if currentstatus == False else 1, 0)
                                    except:
                                        Domoticz.Debug('No mapping for ' + item['code'] + ' skipped')

                            battery_device(unit, item['code'], currentstatus)

    except Exception as err:
        Domoticz.Error('handleThread: ' + str(err)  + ' line ' + format(sys.exc_info()[-1].tb_lineno))

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

# Select device type from category
def DeviceType(category):
    'convert category to device type'
    'https://github.com/tuya/tuya-home-assistant/wiki/Supported-Device-Category'
    if category in {'kg', 'cz', 'pc', 'tdq', 'znjdq', 'szjqr'}:
        result = 'switch'
    elif category in {'dj', 'dd', 'dc', 'fwl', 'xdd', 'fwd', 'jsq', 'tyndj'}:
        result = 'light'
    elif category in {'tgq', 'tgkg'}:
        result = 'dimmer'
    elif category in {'cl', 'clkg', 'jdcljqr'}:
        result = 'cover'
    elif category in {'qn'}:
        result = 'heater'
    elif category in {'wk', 'wkf', 'mjj', 'wkcz'}:
        result = 'thermostat'
    elif category in {'wsdcg', 'co2bj', 'hjjcy', 'qxj'}:
        result = 'sensor'
    elif category in {'rs'}:
        result = 'heatpump'
    elif category in {'znrb'}:
        result = 'smartheatpump'
    elif category in {'sp'}:
        result = 'doorbell'
    elif category in {'fs'}:
        result = 'fan'
    elif category in {'fsd'}:
        result = 'fanlight'
    elif category in {'sgbj'}:
        result = 'siren'
    elif category in {'wnykq'}:
        result = 'smartir'
    elif category in {'zndb', 'dlq'}:
        result = 'powermeter'
    elif category in {'wg2', 'wfcon'}:
        result = 'gateway'
    elif category in {'mcs'}:
        result = 'doorcontact'
    elif category in {'gyd'}:
        result = 'pirlight'
    elif category in {'qt', 'ywbj'}:
        result = 'smokedetector'
    elif category in {'ckmkzq'}:
        result = 'garagedooropener'
    elif category in {'cwwsq'}:
        result = 'feeder'
    elif category in {'sj'}:
        result = 'waterleak'
    elif category in {'pir'}:
        result = 'presence'
    elif category in {'sfkzq'}:
        result = 'irrigation'
    elif category in {'wxkg'}:
        result = 'wswitch'
    elif category in {'dgnbj'}:
        result = 'lightsensor'
    elif category in {'xktyd'}:
        result = 'starlight'
    elif category in {'ms'}:
        result = 'smartlock'
    elif category in {'cs'}:
        result = 'dehumidifier'
    elif category in {'sd'}:
        result = 'vacuum'
    elif category in {'mal'}:
        result = 'multifunctionalarm'
    elif category in {'kj'}:
        result = 'purifier'
    elif category in {'bh'}:
        result = 'smartkettle'
    elif 'infrared_' in category: # keep it last
        result = 'infrared'
    else:
        result = 'unknown'
    return result

def UpdateDevice(ID, Unit, sValue, nValue, TimedOut, AlwaysUpdate = 0):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if str(Devices[ID].Units[Unit].sValue) != str(sValue) or str(Devices[ID].Units[Unit].nValue) != str(nValue) or str(Devices[ID].TimedOut) != str(TimedOut) or AlwaysUpdate == 1:
        if sValue == None:
            sValue = Devices[ID].Units[Unit].sValue
        if type(sValue) == int or type(sValue) == float:
            Devices[ID].Units[Unit].LastLevel = sValue
        elif type(sValue) == dict:
            Devices[ID].Units[Unit].Color = json.dumps(sValue)
        Devices[ID].Units[Unit].sValue = str(sValue)
        Devices[ID].Units[Unit].nValue = nValue
        Devices[ID].TimedOut = TimedOut
        Devices[ID].Units[Unit].Update(Log=True)

        Domoticz.Debug('Update device value: ' + str(ID) + ' Unit: ' + str(Unit) + ' sValue: ' +  str(sValue) + ' nValue: ' + str(nValue) + ' TimedOut=' + str(TimedOut))
    return

def SendCommand(ID, Unit, Status, Type = ''):
    Domoticz.Debug('SendCommand =  ID:' + str(ID) + ' IP:' + str(getConfigItem(ID, 'ip'))  + ' Type:' +  str(Type) + ' Status:' +  str(Status) + ' Status Type:' +  str(type(Status)) + ' Version:' + str(getConfigItem(ID, 'version')))
    if Type == 'light':
        tuya = tinytuya.BulbDevice(dev_id=str(ID), address=str(getConfigItem(ID, 'ip')), local_key=str(getConfigItem(ID, 'key')), version=str(getConfigItem(ID, 'version')), connection_timeout=1, connection_retry_limit=1)
        tuya.detect_available_dps()
        Status = convert_to_correct_type(Status)
        # tuya = tinytuya.BulbDevice(str(ID), getConfigItem(ID, 'ip'), getConfigItem(ID, 'key'))
        # tuya.set_version(str(getConfigItem(ID, 'version')))
        if type(Status) == int or type(Status) == float:
            # Domoticz.Debug('SendCommand: brightness')
            tuya.turn_on(switch=Unit)
            tuya.set_brightness_percentage(Status)
        elif type(Status) == dict:
            if Status['m'] == 2:
                # Domoticz.Debug('SendCommand: colourtemp')
                tuya.turn_on()
                tuya.set_colourtemp(Status['cw'])
            if Status['m'] == 3:
                # Domoticz.Debug('SendCommand: colour')
                # Domoticz.Debug('Colour: r:' + str(Status['r']) + ' g:' + str(Status['g']) + ' b:' + str(Status['r']))
                tuya.turn_on()
                tuya.set_colour(Status['r'], Status['g'], Status['b'])
        elif bool(Status) == True:
            # Domoticz.Debug('SendCommand: On')
            tuya.turn_on()
        elif bool(Status) == False:
            # Domoticz.Debug('SendCommand: Off')
            tuya.turn_off()
        Domoticz.Debug('Command send to tuya BulbDevice: ' + str(ID) + ", " + str({'commands': [{'Type': Type, 'value': Status}]}))
    else:
        tuya = tinytuya.Device(dev_id=str(ID), address=str(getConfigItem(ID, 'ip')), local_key=str(getConfigItem(ID, 'key')), version=str(getConfigItem(ID, 'version')), connection_timeout=1, connection_retry_limit=1)
        tuya.detect_available_dps()
        payload = tuya.generate_payload(tinytuya.CONTROL_NEW, {Unit: Status})
        tuya.send(payload)
        Domoticz.Debug('Command send to tuya Device: ' + str(ID) + ", " + str({'commands': [{'dsp': Unit, 'value': Status}]}))

def searchCode(Item, Functions):
    for OneItem in Functions:
        if Item == OneItem:
            return True
        else:
            return False
    # Domoticz.Debug("searchCodeActualFunction unable to find " + str(Item) + " in " + str(Function))
    return

def createDevice(ID, Unit):
    if ID in Devices:
        if Unit in Devices[ID].Units:
            value = False
        else:
            value = True
    else:
        value = True

    return value

def battery_device(ID, ResultValue, StatusDeviceTuya):
    # Battery_device
    if searchCode('battery_state', ResultValue) or searchCode('battery', ResultValue) or searchCode('va_battery', ResultValue) or searchCode('battery_percentage', ResultValue):
        if searchCode('battery_state', ResultValue):
            if StatusDeviceTuya('battery_state') == 'high':
                currentbattery = 100
            if StatusDeviceTuya('battery_state') == 'middle':
                currentbattery = 50
            if StatusDeviceTuya('battery_state') == 'low':
                currentbattery = 5
        if searchCode('BatteryStatus', ResultValue):
            if int(StatusDeviceTuya('BatteryStatus')) == 1:
                currentbattery = 100
            elif int(StatusDeviceTuya('BatteryStatus')) == 2:
                currentbattery = 50
            elif int(StatusDeviceTuya('BatteryStatus')) == 3:
                currentbattery = 5
            else:
                currentbattery = 100
        if searchCode('battery', ResultValue):
            currentbattery = StatusDeviceTuya('battery') * 10
        if searchCode('va_battery', ResultValue):
            currentbattery = StatusDeviceTuya('va_battery')
        if searchCode('battery_percentage', ResultValue):
            currentbattery = StatusDeviceTuya('battery_percentage')
        if searchCode('residual_electricity', ResultValue):
            currentbattery = StatusDeviceTuya('residual_electricity')
        for unit in Devices[ID].Units:
            if str(currentbattery) != str(Devices[ID].Units[unit].BatteryLevel):
                Devices[ID].Units[unit].BatteryLevel = currentbatter
                Devices[ID].Units[unit].Update()
    return

def online_offline(ID, StatusDeviceTuya):
    for unit in Devices[ID].Units:
        # Domoticz.Debug(str(ID) + '   ' + str(StatusDeviceTuya))
        if str(StatusDeviceTuya) != str(Devices[ID].TimedOut):
            Devices[ID].TimedOut = StatusDeviceTuya
            Devices[ID].Units[unit].Update()
    return

def nextUnit(ID):
    unit = 1
    while unit in Devices(ID) and unit < 255:
        unit = unit + 1
    return unit

def convert_to_correct_type(str_value):
    if isinstance(str_value, dict):
        return str_value
    try:
        # Try converting to int
        return int(str_value)
    except ValueError:
        try:
            # Try converting to float
            return float(str_value)
        except ValueError:
            try:
                # Try converting to bool
                if str_value.lower() == "true":
                    return True
                elif str_value.lower() == "false":
                    return False
                else:
                    # If none of the above, try decoding as JSON
                    return json.loads(str_value)
            except (ValueError, SyntaxError, json.JSONDecodeError):
                try:
                    # Try converting to list
                    return list(ast.literal_eval(str_value))
                except (ValueError, SyntaxError):
                    # If all attempts fail, return the original string
                    return str_value

def ping_ok(sHost) -> bool:
    try:
        subprocess.check_output(
            "ping -{} 1 {}".format("n" if platform.system().lower() == "windows" else "c", sHost), shell=True
        )
    except Exception:
        return False

    return True

def set_scale(device_functions, actual_function_name, raw):
    scale = 0
    if device_functions and actual_function_name:
        for item in device_functions:
            if item['code'] == actual_function_name:
                the_values = item['values']
                scale = int(the_values.get('scale', 0))
                # step = the_values.get('step', 0)
                max = the_values.get('max', 0)
                min = the_values.get('min', 0)
    # set scale
    if scale == 1:
        result = int(raw * 10)
    elif scale == 2:
        result = int(raw * 100)
    elif scale == 3:
        result = int(raw * 1000)
    else:
        result = int(raw)
    # keep between the min and max
    if result > max:
        result = int(max)
        Domoticz.Error('Value higher then maximum device')
    elif result < min:
        result = int(min)
        Domoticz.Error('Value lower then minium device')
    return result

def get_scale(device_functions, actual_function_name, raw):
    scale = 0
    # if actual_function_name == 'temp_current': actual_function_name = 'temp_set'
    if device_functions and actual_function_name:
        for item in device_functions:
            if item['code'] == actual_function_name:
                the_values = item['values']
                scale = the_values.get('scale', 0)
                # step = the_values.get('step', 0)
                unit = the_values.get('unit', 0)
                max = the_values.get('max', 0)
    if scale == 0:
        if unit == 'V' and len(str(max)) >= 4:
            result = float(raw / 10)
        elif unit == 'W' and len(str(max)) >= 5:
            result = float(raw / 10)
        else:
            result = int(raw)
    elif scale == 1:
        result = float(raw / 10)
    elif scale == 2:
        result = float(raw / 100)
    elif scale == 3:
        result = float(raw / 1000)
    else:
        result = int(raw)
    return result

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