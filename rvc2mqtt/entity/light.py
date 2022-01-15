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


class entity(object):
    TOPIC_BASE = "rvc"
    

    def __init__(self, name:str, send_queue: queue):
        self.name: str = name
        self.send_queue = send_queue
        self._topic_string_name = self._prepare_topic_string(name)

        pass

    def _prepare_topic_string(self, input:str) -> str:
        """ convert the string to a consistant value
        
        lower case
        only alphnumeric

        """
        return ''.join(c for c in input.lower() if c.isalnum())
    

    def get_topic_string(self, field:str, state:bool) -> str:
        """ make a topic string for a field.  
        It is either a state topic when you just want status
        Or it is a set topic string if you want to do operations
        """

        s = entity.TOPIC_BASE + "/" + self._topic_string_name + \
            "/" + self._prepare_topic_string(type(self)) + "/" + \
            self._prepare_topic_string(field) + "/"

        if state:
            return s + "status"
        else:
            return s + "set"


class Light(entity):
    LIGHT_ON = "on"
    LIGHT_OFF = "off"


    def __init__(self, name: str, send_quque: queue):
        super.__init__(name, send_quque)
        self.brightnes_command_topic: str = self.make_topic_string("brightness", False)
        self.brightnes_command_topic: str = self.make_topic_string("brightness", False)
        self.brightnes_state_topic: str = self.make_topic_string("brightness", True)
        self.brightnes_command_topic: str = self.make_topic_string("brightness", False)
        pass

    def process_msg(self):
        pass

    def _set_light_state(self, on:bool) -> int:
        # send rvc command
        if on:
            # send on command
            pass
        else:
            # send off command
            pass

        return 0


    def _get_light_state(self) -> str:

        pass

    def _set_brightness_percent(self, percent: float) -> int:
        return 0

    def _get_brightness_percent(self) -> float:
        pass
