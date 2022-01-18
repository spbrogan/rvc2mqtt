"""
A light

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

'''
# Example configuration.yaml entry
light:
  - platform: mqtt
    name: "Office light"
    state_topic: "office/light/status"
    command_topic: "office/light/switch"
    brightness_state_topic: 'office/light/brightness'
    brightness_command_topic: 'office/light/brightness/set'
    qos: 0
    payload_on: "ON"
    payload_off: "OFF"
    optimistic: false
'''




import queue
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass


class LightBaseClass(EntityPluginBaseClass):
    LIGHT_ON = "on"
    LIGHT_OFF = "off"

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        super().__init__(data, mqtt_support)

        # Allow MQTT to control light
        self.set_topic = mqtt_support.make_device_topic_string(self.name, None, False)
        self.mqtt_support.register(self.set_topic, self.process_mqtt_msg)

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        raise NotImplementedError()

    def process_mqtt_msg(self, topic, payload):
        pass


class Light_FromDGN_1FFBD(LightBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"dgn": "1FFBD", "type": "Light"}
    """
    Subclass of light that is tied to RVC DGN of DC_LOAD_STATUS and DC_LOAD_COMMAND
    Supports ON/OFF 

    TODO: can it support brightness

    issue command - Turn on
    {"dgn": "1FFBC", "data": "0200FA0001FF0000", "name": "DC_LOAD_COMMAND", "instance": 2, "group": "00000000",
     "desired level": 125.0,
     "desired operating mode": "00", "desired operating mode definition": "automatic",
     "interlock": "00", "interlock definition": "no interlock active",
     "command": 1, "command definition": "on duration",
     "delay/duration": 255}

    Issue command - Turn off
    {"dgn": "1FFBC", "data": "0100FA0003FF0000", "name": "DC_LOAD_COMMAND", "instance": 1, "group": "00000000",
     "desired level": 125.0,
     "desired operating mode": "00", "desired operating mode definition": "automatic",
     "interlock": "00", "interlock definition": "no interlock active",
     "command": 3, "command definition": "off",
     "delay/duration": 255}

    status - off
    {"dgn": "1FFBD", "data": "0100000000000000", "name": "DC_LOAD_STATUS", "instance": 1, "group": "00000000",
     "operating status": 0.0,
     "operating mode": "00", "operating mode definition": "automatic",
     "variable level capability": "00", "variable level capability definition": "not variable",
     "priority": "0000", "priority definition": "highest priority",
     "delay": 0, "demanded current": 0, "present current": -1600.0}

    status - on
    {"dgn": "1FFBD", "data": "0100C80000000000", "name": "DC_LOAD_STATUS", "instance": 1, "group": "00000000",
     "operating status": 100.0, 
     "operating mode": "00", "operating mode definition": "automatic", 
     "variable level capability": "00", "variable level capability definition": "not variable",
     "priority": "0000", "priority definition": "highest priority",
     "delay": 0, "demanded current": 0, "present current": -1600.0}

    """

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        super().__init__(data, mqtt_support)
        #self.brightness_status_topic = mqtt_support.make_device_topic_string(self.name, "brightness", True)
        #self.brightness_set_topic = mqtt_support.make_device_topic_string(self.name, "brightness", False)
        #mqtt_support.register(self.brightness_set_topic, self.process_mqtt_msg)

        # RVC message must match the following to be this device
        self.rvc_match_status = {
            "dgn": "1FFBD", "instance": data['instance'], "group": data['group']}
        # ignore for now self.rvc_match_command = {"dgn": "1FFBC", "instance": data['instance'], "group": data['group'] }

        # save these for later to send rvc msg
        self.rvc_instance = data['instance']
        self.rvc_group = data['group']
        self.state = "unknown"
        self.brightness = "unknown"

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        # For now only match the status message.

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug("Msg Match Status")
            if new_message["operating status"] == 100.0:
                state = "ON"
            elif new_message["operating status"] == 0.0:
                state = "OFF"
            else:
                state = "UNEXPECTED(" + \
                    str(new_message["operating status"]) + ")"

            self.mqtt_support.client.publish(
                self.status_topic, state, retain=True)
            
            return True
        return False

    def process_mqtt_msg(self, topic, payload):
        pass
