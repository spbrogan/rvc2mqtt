"""
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
import logging
import queue

from rvc2mqtt.mqtt import MQTT_Support

__all__ = ["light"]

class Entity(object):
    """ Baseclass for all entities.
    
    """
      
    def __init__(self, name:str, mqtt_support: MQTT_Support):
        self.name: str = name
        self.Logger = logging.getLogger(__name__)
        self.device_topic = mqtt_support.make_device_topic_root(name)
        self.status_topic = mqtt_support.make_device_topic_string(name, None, True)
        self.set_topic = mqtt_support.make_device_topic_string(name, None, False)
        mqtt_support.register(self, self.set_topic, self.process_mqtt_msg)

    def set_rvc_send_queue(self, send_queue: queue):
        """ Provide queue for sending RVC messages.  Queue requires 
        items be formatted as python-can messages"""
        self.send_queue: queue = send_queue

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.
        
        If relevant - Process the message and return True
        else - return False
        """
        pass

    def process_mqtt_msg(self, topic, payload):
        if topic == self.set_topic:
            self.Logger.info(f"MQTT msg: {topic} {payload}")


from .light import Light

def entity_factory(data: dict, mqtt_support: MQTT_Support) -> Entity:
    if "type" in data:
        t = data["type"].lower()
        name = data["name"]
        if t == "light":
            return Light(name, mqtt_support)
        # Add more here
        else:
          logging.getLogger(__name__).error(f"Unsupported type: {t}")  
    else:
        logging.getLogger(__name__).error(f"Invalid Data: type not defined.  {str(data)}")
    
    return None
    