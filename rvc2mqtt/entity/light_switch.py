"""
A light switch

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


class LightSwitch_DC_LOAD_STATUS(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"name": "DC_LOAD_STATUS", "type": "light_switch"}
    """
    Light switch that is tied to RVC DGN of DC_LOAD_STATUS and DC_LOAD_COMMAND
    Supports ON/OFF 

    TODO: can it support brightness


    """
    LIGHT_ON = "on"
    LIGHT_OFF = "off"

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "light-1FFBD-i" + str(data["instance"])
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # Allow MQTT to control light
        self.command_topic = mqtt_support.make_device_topic_string(
            self.id, None, False)
        self.mqtt_support.register(self.command_topic, self.process_mqtt_msg)

        # RVC message must match the following to be this device
        self.rvc_match_status = { "name": "DC_LOAD_STATUS", "instance": data['instance']}
        self.rvc_match_command= { "name": "DC_LOAD_COMMAND", "instance": data['instance']}

        self.Logger.debug(f"Must match: {str(self.rvc_match_status)} or {str(self.rvc_match_command)}")

        # save these for later to send rvc msg
        self.rvc_instance = data['instance']
        self.rvc_group = '00000000'
        if 'group' in data:
            self.rvc_group = data['group']
        self.name = data['instance_name']
        self.state = "unknown"

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Light from DC_LOAD_STATUS"
                       }     

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")
            if new_message["operating_status"] == 100.0:
                self.state = LightSwitch_DC_LOAD_STATUS.LIGHT_ON
            elif new_message["operating_status"] == 0.0:
                self.state = LightSwitch_DC_LOAD_STATUS.LIGHT_OFF
            else:
                self.state = "UNEXPECTED(" + \
                    str(new_message["operating_status"]) + ")"
                self.Logger.error(
                    f"Unexpected RVC value {str(new_message['operating_status'])}")

            self.mqtt_support.client.publish(
                self.status_topic, self.state, retain=True)
            return True

        elif self._is_entry_match(self.rvc_match_command, new_message):
            # This is the command.  Just eat the message so it doesn't show up
            # as unhandled.
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            return True
        return False

    def process_mqtt_msg(self, topic, payload):
        self.Logger.debug(
            f"MQTT Msg Received on topic {topic} with payload {payload}")

        if topic == self.command_topic:
            if payload.lower() == LightSwitch_DC_LOAD_STATUS.LIGHT_OFF:
                if self.state != LightSwitch_DC_LOAD_STATUS.LIGHT_OFF:
                    self._rvc_light_off()
            elif payload.lower() == LightSwitch_DC_LOAD_STATUS.LIGHT_ON:
                if self.state != LightSwitch_DC_LOAD_STATUS.LIGHT_ON:
                    self._rvc_light_on()
            else:
                self.Logger.warning(
                    f"Invalid payload {payload} for topic {topic}")

    def _rvc_light_off(self):
        # 01 00 FA 00 03 FF 0000
        msg_bytes = bytearray(8)
        struct.pack_into("<BBBBBBH", msg_bytes, 0, self.rvc_instance, int(
            self.rvc_group, 2), 250, 0, 3, 0xFF, 0)
        self.send_queue.put({"dgn": "1FFBC", "data": msg_bytes})

    def _rvc_light_on(self):

        # 01 00 FA 00 01 FF 0000
        msg_bytes = bytearray(8)
        struct.pack_into("<BBBBBBH", msg_bytes, 0, self.rvc_instance, int(
            self.rvc_group, 2), 250, 0, 1, 0xFF, 0)
        self.send_queue.put({"dgn": "1FFBC", "data": msg_bytes})

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data

        """

        # produce the HA MQTT discovery config json
        config = {"name": self.name, 
                  "state_topic": self.status_topic,
                  "command_topic": self.command_topic,
                  "qos": 1, "retain": False,
                  "payload_on": LightSwitch_DC_LOAD_STATUS.LIGHT_ON,
                  "payload_off": LightSwitch_DC_LOAD_STATUS.LIGHT_OFF,
                  "unique_id": self.unique_device_id,
                  "device": self.device}

        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "switch")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_topic, self.state, retain=True)

        # request dgn report - this should trigger that light to report
        # dgn = 1FFBD which is actually  BD FF 01 <instance> FF 00 00 00
        self.Logger.debug("Sending Request for DGN")
        data = struct.pack("<BBBBBBBB", int("0xBD", 0), int(
            "0xFF", 0), 1, self.rvc_instance, 0, 0, 0, 0)
        self.send_queue.put({"dgn": "EAFF", "data": data})
