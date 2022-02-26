"""
Water Heater support

1 - Power On / Off switch
2 - Running Status (running , not running)
3 - Sensor: water hookup external hookup (yes/no)
4 - Sensor - System Pressure

Copyright 2022 Sean Brogan
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""


import queue
import logging
import struct
import json
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass

'''


 Water Heater Command
This DGN provides external control of the water heater. Table 6.9.3a defines the DG attributes, and Table 6.9.3b defines the 
signal and parameter attributes.
An instance of zero indicates that the settings should be applied to all water heater instances. Values of 255 (or 65535) indicate 
that the particular datum should not be changed

'''

class WaterHeaterClass(EntityPluginBaseClass):
    '''
    Water Heater based on WATERHEATER_STATUS and WATERHEATER_COMMAND DGNs
    Multi instance device

    switch:  
        AC on/off
        Gas on/off

    input: 
        set point temp

    Sensor:
        Water Temp

    Binary Sensor: 
        
        Thermostat Met/Not Met
        Gas Burner Active
        AC Element Active
        High Temp Tripped

        Failure Gas
        Failure AC power
        Failure DC power
        failure DC Warning

    
    '''
    FACTORY_MATCH_ATTRIBUTES = {"name": "WATERHEATER_STATUS", "type": "waterheater"}
    ON = "on"
    OFF = "off"

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = f"waterheater-i" + str(data["instance"])

        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following status or command
        self.rvc_match_status = {"name": "WATERHEATER_STATUS", "instance": data['instance']}
        self.rvc_match_command = {"name": "WATERHEATER_COMMAND", "instance": data['instance']}
        self.rvc_match_command2 = {"name": "WATERHEATER_COMMAND2", "instance": data['instance']}

        self.Logger.debug(f"Must match: {str(self.rvc_match_status)} {str(self.rvc_match_command)} {str(self.rvc_match_command2)}")
        
        # fields for a water heater object
        self.name = data["instance_name"]
        self.instance = data['instance']
        self.mode = "unknown"  # R/W mqtt and RVC (off, combustion, electric, gas/electric, auto, test gas, test electric )
        self.gas_mode = "unknown"
        self.ac_mode = "unknown"
        self.set_point_temperature = "unknown" # R/W mqtt and RVC (deg c)
        self.water_temperature = "unknown" # RO mqtt and RVC (deg c)
        self.thermostat_status = "unknown" # RO mqtt and RVC (met / not met)
        self.burner_status = "unknown" # RO mqtt and RVC (off, lit)
        self.ac_element_status = "unknown" # RO mqtt and RVC (AC inactive, AC active)
        self.high_temp_switch_status = "unknown" # RO mqtt and RVC (tripped, not tripped)
        self.failure_to_ignite = "unknown" # RO mqtt and RVC (no failure, failure)
        self.failure_ac_power = "unknown" # RO mqtt and RVC (power present, power not present) 
        self.failure_dc_power = "unknown" # RO mqtt and RVC (power present, power not present)
        self.failure_dc_warning = "unknown" # RO mqtt and RVC (power ok, power low)

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Water Heater from WATERHEATER_STATUS"
                       }

        # Allow MQTT to control gas - on off
        self.status_gas_topic = mqtt_support.make_device_topic_string(self.id, "gas", True)
        self.command_gas_topic = mqtt_support.make_device_topic_string(self.id, "gas", False)
        self.mqtt_support.register(self.command_gas_topic, self.process_mqtt_msg)

        # Allow MQTT to control ac electric - on off
        self.status_ac_topic = mqtt_support.make_device_topic_string(self.id, "ac", True)
        self.command_ac_topic = mqtt_support.make_device_topic_string(self.id, "ac", False)
        self.mqtt_support.register(self.command_ac_topic, self.process_mqtt_msg)

        # Allow MQTT to control set point temperature
        self.status_set_point_temp_topic = mqtt_support.make_device_topic_string(self.id, "set_point_temperature", True)
        self.command_set_point_temp_topic = mqtt_support.make_device_topic_string(self.id, "set_point_temperature", False)
        self.mqtt_support.register(self.command_set_point_temp_topic, self.process_mqtt_msg)

        # water temp
        self.status_water_temp_topic = mqtt_support.make_device_topic_string(self.id, "water_temperature", True)

        # thermostat 
        self.status_thermostat_topic = mqtt_support.make_device_topic_string(self.id, "thermostat", True)

        # Gas Burner status
        self.status_gas_burner_topic = mqtt_support.make_device_topic_string(self.id, "gas_burner", True)

        # AC/Electric element status
        self.status_ac_element_topic = mqtt_support.make_device_topic_string(self.id, "ac_element", True)

        # High temp switch status
        self.status_high_temp_topic = mqtt_support.make_device_topic_string(self.id, "high_temp", True)

        self.status_failure_gas_topic = mqtt_support.make_device_topic_string(self.id, "failure_gas", True)
        self.status_failure_ac_topic = mqtt_support.make_device_topic_string(self.id, "failure_ac", True)
        self.status_failure_dc_topic = mqtt_support.make_device_topic_string(self.id, "failure_dc", True)
        self.status_failure_low_dc_topic = mqtt_support.make_device_topic_string(self.id, "failure_low_dc", True)




    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        '''
        {'arbitration_id': '0x19fff780', 'data': '0100000000000000', 'priority': '6',
        'dgn_h': '1FF', 'dgn_l': 'F7', 'dgn': '1FFF7', 'source_id': '80',
        'name': 'WATERHEATER_STATUS', 'instance': 1,
        'operating_modes': 0, 'operating_modes_definition': False, 
        'set_point_temperature': -273.0, 
        'water_temperature': -273.0, 
        'thermostat_status': '00', 'thermostat_status_definition': 'set point met', 
        'burner_status': '00', 'burner_status_definition': False,
        'ac_element_status': '00', 'ac_element_status_definition': 'no fault', 
        'high_temperature_limit_switch_status': '00', 'high_temperature_limit_switch_status_definition': 'limit switch not tripped',
        'failure_to_ignite_status': '00', 'failure_to_ignite_status_definition': 'no failure',
        'ac_power_failure_status': '00', 'ac_power_failure_status_definition': 'ac power present',
        'dc_power_failure_status': '00', 'dc_power_failure_status_definition': 'dc power present'}
        '''

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")

            # Op Mode State
            self.mode = new_message["operating_modes"]
            self.gas_mode = WaterHeaterClass.OFF
            self.ac_mode = WaterHeaterClass.OFF 
            if new_message["operating_modes"] in [1, 3, 4, 5]:
                self.gas_mode = WaterHeaterClass.ON
            if new_message["operating_modes"] in [2, 3, 4, 6]:
                self.ac_mode = WaterHeaterClass.ON
            
            if new_message["operating_modes"] > 7:
                self.Logger.error(
                    f"Unexpected RVC Mode Value {str(self.mode)}")

            self.mqtt_support.client.publish(self.status_topic, self.mode, retain=True)
            self.mqtt_support.client.publish(self.status_gas_topic, self.gas_mode, retain=True)
            self.mqtt_support.client.publish(self.status_ac_topic, self.ac_mode, retain=True)

            # Set Point Temperature
            self.set_point_temperature = new_message["set_point_temperature"]
            self.mqtt_support.client.publish(self.status_set_point_temp_topic, self.set_point_temperature, retain=True)

            # water temperature
            self.water_temperature = new_message["water_temperature"]
            self.mqtt_support.client.publish(self.status_water_temp_topic, self.water_temperature, retain=True)

            # Thermostat
            if new_message["thermostat_status"] == '00':
                self.thermostat_status = WaterHeaterClass.OFF
            elif new_message["thermostat_status"] == '01':
                self.thermostat_status = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC thermostat status value {new_message['thermostat_status']}")
            self.mqtt_support.client.publish(self.status_thermostat_topic, self.thermostat_status, retain=True)

            # Gas Burner
            if new_message["burner_status"] == '00':
                self.burner_status = WaterHeaterClass.OFF
            elif new_message["burner_status"] == '01':
                self.burner_status = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC burner status value {new_message['burner_status']}")
            self.mqtt_support.client.publish(self.status_gas_burner_topic, self.burner_status, retain=True)

            # AC Element
            if new_message["ac_element_status"] == '00':
                self.ac_element_status = WaterHeaterClass.OFF
            elif new_message["ac_element_status"] == '01':
                self.ac_element_status = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC ac element status value {new_message['ac_element_status']}")
            self.mqtt_support.client.publish(self.status_ac_element_topic, self.ac_element_status, retain=True)

            # High Temp Limit Tripped
            if new_message["high_temperature_limit_switch_status"] == '00':
                self.high_temp_switch_status = WaterHeaterClass.OFF
            elif new_message["high_temperature_limit_switch_status"] == '01':
                self.high_temp_switch_status = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC high temp limit switch status value {new_message['high_temperature_limit_switch_status']}")
            self.mqtt_support.client.publish(self.status_high_temp_topic, self.high_temp_switch_status, retain=True)

            # Failure To Ignite (gas)
            if new_message["failure_to_ignite_status"] == '00':
                self.failure_to_ignite = WaterHeaterClass.OFF
            elif new_message["failure_to_ignite_status"] == '01':
                self.failure_to_ignite = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC failure to ignite status value {new_message['failure_to_ignite_status']}")
            self.mqtt_support.client.publish(self.status_failure_gas_topic, self.failure_to_ignite, retain=True)

            # Failure AC element
            if new_message["ac_power_failure_status"] == '00':
                self.failure_ac_power = WaterHeaterClass.OFF
            elif new_message["ac_power_failure_status"] == '01':
                self.failure_ac_power = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC ac power failure status value {new_message['ac_power_failure_status']}")
            self.mqtt_support.client.publish(self.status_failure_ac_topic, self.failure_ac_power, retain=True)

            # Failure DC Power
            if new_message["dc_power_failure_status"] == '00':
                self.failure_dc_power = WaterHeaterClass.OFF
            elif new_message["dc_power_failure_status"] == '01':
                self.failure_dc_power = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC dc power failure status value {new_message['dc_power_failure_status']}")
            self.mqtt_support.client.publish(self.status_failure_dc_topic, self.failure_dc_power, retain=True)

            # Failure Warning DC Power (power low)
            if new_message["dc_power_warning_status"] == '00':
                self.failure_dc_warning = WaterHeaterClass.OFF
            elif new_message["dc_power_warning_status"] == '01':
                self.failure_dc_warning = WaterHeaterClass.ON
            else:
                self.Logger.error(f"Unexpected RVC dc power warning failure status value {new_message['dc_power_warning_status']}")
            self.mqtt_support.client.publish(self.status_failure_low_dc_topic, self.failure_dc_warning, retain=True)

            return True

        elif self._is_entry_match(self.rvc_match_command, new_message):
            # This is the command.  Just eat the message so it doesn't show up
            # as unhandled.
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            return True

        elif self._is_entry_match(self.rvc_match_command2, new_message):
            # This is the command2.  Just eat the message so it doesn't show up
            # as unhandled.
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            return True
        return False

    def process_mqtt_msg(self, topic, payload):
        """ mqtt message:
                Turn Gas On/Off
                Turn AC element On/Off
                Set Water Temp Set point
                
        """
        
        self.Logger.debug(f"MQTT Msg Received on topic {topic} with payload {payload}")

        if topic == self.command_ac_topic:
            if payload.lower() == WaterHeaterClass.OFF:
                if self.ac_mode != WaterHeaterClass.OFF:
                    self._rvc_change_mode(self.gas_mode == WaterHeaterClass.ON, False)
            elif payload.lower() == WaterHeaterClass.ON:
                if self.ac_mode != WaterHeaterClass.ON:
                    self._rvc_change_mode(self.gas_mode == WaterHeaterClass.ON, True)      
            else:
                self.Logger.error(
                    f"Invalid payload {payload} for topic {topic}")

        elif topic == self.command_gas_topic:
            if payload.lower() == WaterHeaterClass.OFF:
                if self.gas_mode != WaterHeaterClass.OFF:
                    self._rvc_change_mode(False, self.ac_mode == WaterHeaterClass.ON)
            elif payload.lower() == WaterHeaterClass.ON:
                if self.gas_mode != WaterHeaterClass.ON:
                    self._rvc_change_mode(True, self.ac_mode == WaterHeaterClass.ON)     
            else:
                self.Logger.error(
                    f"Invalid payload {payload} for topic {topic}")

        elif topic == self.command_set_point_temp_topic:
            try:
                temperature = float(payload)
                self._rvc_change_set_point(temperature)
            except Exception as e:
                self.Logger.error(f"Invalid payload {payload} for topic {topic}")

    def _rvc_change_mode(self, gas_on: bool, ac_on: bool):
        ''' change the mode of the water heater.  This can be off/electic on/gas on/both on'''
        mode = 0

        if gas_on:
            if ac_on:
                mode = 3
            else:
                mode = 1
        else:
            if ac_on:
                mode = 2
            else:
                mode = 0

        self.Logger.debug(f"Set Mode to {mode}")

        #Waterheater_command
        # electic
        # 0102000000000000

        # gas
        # 0101000000000000

        # gas and electric
        # 0103000000000000

        # off
        # 0100000000000000
        msg_bytes = bytearray(8)
        struct.pack_into("<BBHBBBB", msg_bytes, 0, self.instance, mode, 0, 0, 0, 0, 0)
        self.send_queue.put({"dgn": "1FFF6", "data": msg_bytes})

    def _rvc_change_set_point(self, temp: float):
        self.Logger.debug(f"Set hotwater set point to {temp}")
        raise NotImplementedError()

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data

        """

        # Gas switch - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Gas",
                  "state_topic": self.status_gas_topic,
                  "command_topic": self.command_gas_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_gas_mode",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "switch", "gas_mode")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_gas_topic, self.gas_mode, retain=True)

        # AC element switch - produce the HA MQTT discovery config json for
        config = {"name": self.name + " AC", "state_topic": self.status_ac_topic,
                  "command_topic": self.command_ac_topic, "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON, "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_electric_mode",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "switch", "electric_mode")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_ac_topic, self.ac_mode, retain=True)

        # Set Point Temp input - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Set Point Temperature", "state_topic": self.status_set_point_temp_topic,
                  "command_topic": self.command_set_point_temp_topic, "qos": 1, "retain": False,
                  "unit_of_meas": '°C',
                  "device_class": "temperature",
                  "state_class": "measurement",
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "value_template": '{{value}}',
                  "unique_id": self.unique_device_id + "_set_point_temperature",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "number", "set_point_temperature")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_set_point_temp_topic, self.set_point_temperature, retain=True)


        # Water Temperature sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Water Temperature", "state_topic": self.status_water_temp_topic,
                  "qos": 1, "retain": False,
                   "unit_of_meas": '°C',
                  "device_class": "temperature",
                  "state_class": "measurement",
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "value_template": '{{value}}',
                  "unique_id": self.unique_device_id + "_water_temperature",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "sensor", "water_temperature")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_water_temp_topic, self.water_temperature, retain=True)


        # thermostat status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Thermostat Status", "state_topic": self.status_thermostat_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON, "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_thermostat",
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "thermostat")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_thermostat_topic, self.thermostat_status, retain=True)


        # Gas Burner Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Gas Burner" , "state_topic": self.status_gas_burner_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "unique_id": self.unique_device_id + "_gas_burner_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "gas_burner_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_gas_burner_topic, self.burner_status, retain=True)

        # AC Element Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " AC Element" , "state_topic": self.status_ac_element_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "unique_id": self.unique_device_id + "_ac_element_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "ac_element_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_ac_element_topic, self.ac_element_status, retain=True)

        # High temp limit switch Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " High-Temp Limit" , "state_topic": self.status_high_temp_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "unique_id": self.unique_device_id + "_high_temp_limit_switch_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "high_temp_limit_switch_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_high_temp_topic, self.high_temp_switch_status, retain=True)

        # Failure to ignite Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " Gas Igniter Failure" , "state_topic": self.status_failure_gas_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_failure_to_ignite_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "failure_to_ignite_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_failure_gas_topic, self.failure_to_ignite, retain=True)

        # Failure AC Power Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " AC Power Failure" , "state_topic": self.status_failure_ac_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_failure_ac_power_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "failure_ac_power_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_failure_ac_topic, self.failure_ac_power, retain=True)

        # Failure DC Power Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " DC Power Failure" , "state_topic": self.status_failure_dc_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_failure_dc_power_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "failure_dc_power_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_failure_dc_topic, self.failure_dc_power, retain=True)

        # Failure DC Power warning Status binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " DC Low Power Warning" , "state_topic": self.status_failure_low_dc_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterHeaterClass.ON,
                  "payload_off": WaterHeaterClass.OFF,
                  "unique_id": self.unique_device_id + "_failure_dc_power_warning_status",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "failure_dc_power_warning_status")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_failure_low_dc_topic, self.failure_dc_warning, retain=True)