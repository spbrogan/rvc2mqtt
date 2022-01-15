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

__all__ = ["light"]

class Entity(object):
    """ Baseclass for all entities.
    
    """
    TOPIC_BASE = "rvc"    

    def __init__(self, name:str):
        self.name: str = name
        self._topic_string_name = self._prepare_topic_string(name)

        pass

    def set_rvc_send_queue(self, send_queue: queue):
        self.send_queue: queue = send_queue

    def set_mqtt_subscriptions(self):
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

        s = Entity.TOPIC_BASE + "/" + self._topic_string_name + \
            "/" + self._prepare_topic_string(type(self)) + "/" + \
            self._prepare_topic_string(field) + "/"

        if state:
            return s + "status"
        else:
            return s + "set"

    def process_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.
        
        If relevant - Process the message and return True
        else - return False
        """
        pass


from .light import Light

def entity_factory(data: dict) -> Entity:
    if "type" in data:
        t = data["type"].lower()
        if t == "light":
            return Light()
        # Add more here
        else:
          logging.getLogger(__name__).error(f"Unsupported type: {t}")  
    else:
        logging.getLogger(__name__).error(f"Invalid Data: type not defined.  {str(data)}")
    
    return None
    