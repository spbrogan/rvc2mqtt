"""
Water Pump support

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
 {'arbitration_id': '0x19ffb380', 'data': '0000000000000000',
  'priority': '6', 'dgn_h': '1FF', 'dgn_l': 'B3', 'dgn': '1FFB3',
  'source_id': '80', 'name': 'WATER_PUMP_STATUS',
  'operating_status': '00', 'operating_status_definition': 'pump disabled', 
  'pump_status': '00', 'pump_status_definition': 'pump not running',
  'water_hookup_detected': '00', 'water_hookup_detected_definition': 'outside water connected',
  'current_system_pressure': 0, 'pump_pressure_setting': 0,
  'regulator_pressure_setting': 0, 'operating_current': 0}
'''


class WaterPumpClass(EntityPluginBaseClass):
    '''
    Water pump switch, status, and pressure sensors based
    on the Water Pump Status / Command RV-C DGN
    '''
    FACTORY_MATCH_ATTRIBUTES = {
        "name": "WATER_PUMP_STATUS", "type": "water_pump"}
    ON = "on"
    OFF = "off"
    OUTSIDE_WATER_CONNECTED = "connected"
    OUTSIDE_WATER_DISCONNECTED = "disconnected"

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "waterpump-wps"  # for now it seems water pump is a singleton in RV

        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following status or command
        self.rvc_match_status = {"name": "WATER_PUMP_STATUS"}
        self.rvc_match_command = {"name": "WATER_PUMP_COMMAND"}

        self.Logger.debug(
            f"Must match: {str(self.rvc_match_status)} {str(self.rvc_match_command)}")

        # fields for a water pump object
        self.name = data["instance_name"]
        self.power_state = "unknown"  # R/W mqtt and RVC
        self.running_state = "unknown"  # RO mqtt and RVC
        self.external_water_hookup = "unknown"  # RO mqtt and RVC
        # RO mqtt and RVC (this is configurable but ignore for now as i don't think my trailer supports it)
        self.system_pressure = 0.0

        # Allow MQTT to control power
        self.command_topic = mqtt_support.make_device_topic_string(
            self.id, None, False)
        self.running_status_topic = mqtt_support.make_device_topic_string(
            self.id, "running", True)
        self.external_water_status_topic = mqtt_support.make_device_topic_string(
            self.id, "external_water", True)
        self.system_pressure_status_topic = mqtt_support.make_device_topic_string(
            self.id, "system_pressure", True)
        self.mqtt_support.register(self.command_topic, self.process_mqtt_msg)

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Waterpump from WATER_PUMP_STATUS"
                       }

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")

            # Power State
            if new_message["operating_status"] == "01":
                self.power_state = WaterPumpClass.ON
            elif new_message["operating_status"] == "00":
                self.power_state = WaterPumpClass.OFF
            else:
                self.power_state = "UNEXPECTED(" + \
                    str(new_message["operating_status"]) + ")"
                self.Logger.error(
                    f"Unexpected RVC value {str(new_message['operating_status'])}")

            self.mqtt_support.client.publish(
                self.status_topic, self.power_state, retain=True)

            # Running State
            if new_message["pump_status"] == "01":
                self.running_state = WaterPumpClass.ON
            elif new_message["pump_status"] == "00":
                self.running_state = WaterPumpClass.OFF
            else:
                self.running_state = "UNEXPECTED(" + \
                    str(new_message["pump_status"]) + ")"
                self.Logger.error(
                    f"Unexpected RVC value {str(new_message['pump_status'])}")

            self.mqtt_support.client.publish(
                self.running_status_topic, self.running_state, retain=True)

            # External Water Hookup State
            if new_message["water_hookup_detected"] == "01":
                self.external_water_hookup = WaterPumpClass.OUTSIDE_WATER_DISCONNECTED
            elif new_message["water_hookup_detected"] == "00":
                self.external_water_hookup = WaterPumpClass.OUTSIDE_WATER_CONNECTED
            else:
                self.external_water_hookup = "UNEXPECTED(" + \
                    str(new_message["water_hookup_detected"]) + ")"
                self.Logger.error(
                    f"Unexpected RVC value {str(new_message['water_hookup_detected'])}")

            self.mqtt_support.client.publish(
                self.external_water_status_topic, self.external_water_hookup, retain=True)

            # System Pressure
            self.system_pressure = new_message['current_system_pressure']
            self.mqtt_support.client.publish(
                self.system_pressure_status_topic, self.system_pressure, retain=True)

            return True

        elif self._is_entry_match(self.rvc_match_command, new_message):
            # This is the command.  Just eat the message so it doesn't show up
            # as unhandled.
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            return True
        return False

    def process_mqtt_msg(self, topic, payload):
        """ mqtt message to turn on or off the power switch for the pump"""

        self.Logger.debug(
            f"MQTT Msg Received on topic {topic} with payload {payload}")

        if topic == self.command_topic:
            if payload.lower() == WaterPumpClass.OFF:
                if self.power_state != WaterPumpClass.OFF:
                    self._rvc_pump_off()
            elif payload.lower() == WaterPumpClass.ON:
                if self.power_state != WaterPumpClass.ON:
                    self._rvc_pump_on()
            else:
                self.Logger.warning(
                    f"Invalid payload {payload} for topic {topic}")

    def _rvc_pump_off(self):
        msg_bytes = bytearray(8)
        struct.pack_into("<BHHBBB", msg_bytes, 0, 0, 0, 0, 0, 0, 0)
        self.Logger.debug("Turn Pump Off")
        self.send_queue.put({"dgn": "1FFB2", "data": msg_bytes})

    def _rvc_pump_on(self):
        msg_bytes = bytearray(8)
        struct.pack_into("<BHHBBB", msg_bytes, 0, 1, 0, 0, 0, 0, 0)
        self.Logger.debug("Turn Pump On")
        self.send_queue.put({"dgn": "1FFB2", "data": msg_bytes})

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data

        """

        # power state switch - produce the HA MQTT discovery config json for
        config = {"name": self.name + " power",
                  "state_topic": self.status_topic,
                  "command_topic": self.command_topic, "qos": 1, "retain": False,
                  "payload_on": WaterPumpClass.ON,
                  "payload_off": WaterPumpClass.OFF,
                  "unique_id": self.unique_device_id + "_power",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "switch", "power")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_topic, self.power_state, retain=True)

        # running state binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " running status",
                  "state_topic": self.running_status_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterPumpClass.ON,
                  "payload_off": WaterPumpClass.OFF,
                  "enabled_by_default": False,  # this implementation running is the same as power
                  "unique_id": self.unique_device_id + "_running",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "running")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.running_status_topic, self.running_state, retain=True)

        # External Water Connected binary sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " external water",
                  "state_topic": self.external_water_status_topic,
                  "qos": 1, "retain": False,
                  "payload_on": WaterPumpClass.OUTSIDE_WATER_CONNECTED,
                  "payload_off": WaterPumpClass.OUTSIDE_WATER_DISCONNECTED,
                  "unique_id": self.unique_device_id + "_external_water",
                  "enabled_by_default": False,  # this sensor is just the opposite of running/power
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "binary_sensor", "external_water")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.external_water_status_topic, self.external_water_hookup, retain=True)

        # System Pressure sensor  - produce the HA MQTT discovery config json for
        config = {"name": self.name + " system pressure", 
                  "state_topic": self.system_pressure_status_topic,
                  "qos": 1, "retain": False,
                  "unit_of_meas": 'Pa',
                  "device_class": "pressure",
                  "state_class": "measurement",
                  "value_template": '{{value}}',
                  "unique_id": self.unique_device_id + "_system_pressure",
                  "enabled_by_default": False,  # this implementation doesn't expect this sensor to be used
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "sensor", "system_pressure")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.system_pressure_status_topic, self.system_pressure, retain=True)
