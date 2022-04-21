"""
An on/off + dimmer light

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


class Light_DC_LOAD_STATUS(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"name": "DC_LOAD_STATUS", "type": "light"}
    """
    light that is tied to RVC DGN of DC_LOAD_STATUS and DC_LOAD_COMMAND
    Supports ON/OFF and dimmer

    See: https://www.home-assistant.io/integrations/light.mqtt/

    """
    _ON = "on"
    _OFF = "off"
    _UNKNOWN = "unknown"

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "light-1FFBD-i" + str(data["instance"])
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # Allow MQTT to control on/off
        self.command_topic = mqtt_support.make_device_topic_string(
            self.id, None, False)
        self.mqtt_support.register(self.command_topic, self.process_mqtt_msg)

        # Allow MQTT to control brightness
        self.status_brightness_topic = mqtt_support.make_device_topic_string(self.id, "brightness", True)
        self.command_brightness_topic = mqtt_support.make_device_topic_string(self.id, "brightness", False)
        self.mqtt_support.register(self.command_brightness_topic, self.process_mqtt_msg)

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
        self._state = Light_DC_LOAD_STATUS._UNKNOWN
        self._brightness = 0
        self.brightness_support = False
        self._changed = True

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Light from DC_LOAD_STATUS"
                       }  

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value != self._state:
            self._state = value
            self._changed = True 

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int):
        if value < 0 or value > 100:
            return

        if value != self._brightness:
            self._brightness = value
            self._changed = True

    @property
    def rvc_brightness(self) -> int:
        if self._brightness == 100:
            # special value for 100% 
            return 250
        return int((self._brightness/100) * 200)
    
    @rvc_brightness.setter
    def rvc_brightness(self, value:int):
        if value < 0 or value > 250:
            return
        
        v = int(min(value * 0.5, 100))
        if v != self._brightness:
            self._brightness = v
            self._changed = True


    

    # turn off
    # 2022-04-21 07:11:11 {'arbitration_id': '0x19ffbc44', 
    # 'data': '0100FA0003FF0000', 'priority': '6', 'dgn_h': '1FF', 'dgn_l': 'BC', 'dgn': '1FFBC', 'source_id': '44', 'name': 'DC_LOAD_COMMAND',
    # 'instance': 1, 'group': '00000000', 'desired_level': 125.0, 
    # 'desired_operating_mode': '00', 'desired_operating_mode_definition': 'automatic',
    #  'interlock': '00', 'interlock_definition': 'no interlock active', 'command': 3, 'command_definition': 'off',
    #  'delay_duration': 255}

    # response
    # 2022-04-21 07:11:11 {'arbitration_id': '0x19ffbd80', 'data': '0100000000000000', 'priority': '0000',
    #  'dgn_h': '1FF', 'dgn_l': 'BD', 'dgn': '1FFBD', 'source_id': '80', 'name': 'DC_LOAD_STATUS',
    #  'instance': 1, 'group': '00000000', 'operating_status': 0.0,
    #  'operating_mode': '00', 'operating_mode_definition': 'automatic', 
    # 'variable_level_capability': '00', 'variable_level_capability_definition': 'not variable', 
    # 'priority_definition': 'highest priority', 'delay': 0, 'demanded_current': 0, 'present_current': -1600.0}


    # Turn on
    # 2022-04-21 07:11:07 {'arbitration_id': '0x19ffbc44', 'data': '0100FA0001FF0000', 
    # 'priority': '6', 'dgn_h': '1FF', 'dgn_l': 'BC', 'dgn': '1FFBC', 'source_id': '44', 'name': 'DC_LOAD_COMMAND',
    #  'instance': 1, 'group': '00000000', 'desired_level': 125.0,
    #  'desired_operating_mode': '00', 'desired_operating_mode_definition': 'automatic',
    #  'interlock': '00', 'interlock_definition': 'no interlock active',
    #  'command': 1, 'command_definition': 'on duration', 'delay_duration': 255}

    # Response
    # 2022-04-21 07:11:07 {'arbitration_id': '0x19ffbd80', 'data': '0100C80000000000', 'priority': '0000',
    #  'dgn_h': '1FF', 'dgn_l': 'BD', 'dgn': '1FFBD', 'source_id': '80', 'name': 'DC_LOAD_STATUS',
    #  'instance': 1, 'group': '00000000', 'operating_status': 100.0,
    #  'operating_mode': '00', 'operating_mode_definition': 'automatic', 'variable_level_capability': '00',
    # 'variable_level_capability_definition': 'not variable', 'priority_definition': 'highest priority', 'delay': 0,
    #  'demanded_current': 0, 'present_current': -1600.0}




    def _update_mqtt_topics_with_changed_values(self):
        if self._changed:            
            self.mqtt_support.client.publish(self.status_topic, self.state, retain=True)
            self.mqtt_support.client.publish(self.status_brightness_topic, self.brightness, retain=True)
            self._changed = False


    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")
            if new_message["operating_status"] > 0.0:
                self.state = Light_DC_LOAD_STATUS._ON
            else:
                self.state = Light_DC_LOAD_STATUS._OFF
            
            # RVC message layer is already translating to a % so set brightness based on that
            self.brightness = min(int(new_message["operating_status"]), 100)

            if not self._discovered:
                self.brightness_support = new_message["variable_level_capability_definition"] == '01'
                self._publish_ha_light_config()
            
            self._update_mqtt_topics_with_changed_values()

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
            self.state = payload.lower()
        elif topic == self.command_brightness_topic:
            self.brightness = int(payload)
        else:
            self.Logger.error(f"Unsupported MQTT topic {topic}")
            return

        self._send_rvc()

    def _send_rvc(self):
        v = 0
        command = 3  # off
        if self.state == Light_DC_LOAD_STATUS._ON:
            v = self.rvc_brightness
            if self.brightness_support:
                ## WARNING - This is untested as i don't have any dimmable lights
                command = 0 # Set Level
            else:
                command = 1 # on duration
        elif self.state == Light_DC_LOAD_STATUS._OFF:
            command = 3 # off

        msg_bytes = bytearray(8)
        struct.pack_into("<BBBBBBH", msg_bytes, 0, self.rvc_instance, int(self.rvc_group, 2), v, 0, command, 0xFF, 0)
        self.send_queue.put({"dgn": "1FFBC", "data": msg_bytes})


    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data

        """
        # request dgn report - this should trigger that light to report
        # dgn = 1FFBD which is actually  BD FF 01 <instance> FF 00 00 00
        self.Logger.debug("Sending Request for DGN")
        data = struct.pack("<BBBBBBBB", int("0xBD", 0), int(
            "0xFF", 0), 1, self.rvc_instance, 0, 0, 0, 0)
        self.send_queue.put({"dgn": "EAFF", "data": data})

    def _publish_ha_light_config(self):
        """ Will publish the config once we know if know more info

        """

        # produce the HA MQTT discovery config json
        config = {"name": self.name, 
                  "state_topic": self.status_topic,
                  "command_topic": self.command_topic,

                  "qos": 1, "retain": False,
                  "payload_on": Light_DC_LOAD_STATUS._ON,
                  "payload_off": Light_DC_LOAD_STATUS._OFF,
                  "unique_id": self.unique_device_id,
                  "device": self.device}

        if self.brightness_support:
            config.update( {"brightness_state_topic": self.status_brightness_topic,
                  "brightness_command_topic": self.command_brightness_topic,
                  "brightness_command_template": "{{value}}",
                  "brightness_value_template": "{{value}}",
                  "brightness_scale": 100,  # max brightness is 100
            })

        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "light")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)
        self.mqtt_support.client.publish(
            self.status_topic, self.state, retain=True)
