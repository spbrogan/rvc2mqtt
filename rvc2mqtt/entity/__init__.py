"""

EntityPluginBaseClass

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

class EntityPluginBaseClass(object):
    """ Baseclass for all device entities
    
    Make a subclass for a new object
    and define 

    """  
    def __init__(self, data:dict, mqtt_support: MQTT_Support):

        if not hasattr(self, "id"):
            # this seems like a bad code pattern..but ok for now
            raise Exception("self.id must be defined")
        
        self.Logger = logging.getLogger(__class__.__name__)
        self.mqtt_support: MQTT_Support = mqtt_support

        # Make the required one status/state topic
        self.status_topic: str = mqtt_support.make_device_topic_string(self.id, None, True)
        self.unique_device_id = mqtt_support.TOPIC_BASE + "_" + mqtt_support.client_id + "_" + self.id 

        self.link_id = None     # id for this entity so if other objects want a link
        if "link_id" in data:
            self.link_id = data["link_id"]

        self.entity_links = [] # list of link_ids that this object needs a reference to once the entity has been created
        if "entity_links" in data:
            self.entity_links.extend(data["entity_links"])


    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming rvc message and determine if it
        is of interest to this instance of this object.
        
        If relevant - Process the message and return True
        else - return False
        """
        raise NotImplementedError()

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  
        
        This can be a good place to request data
        """
        pass
    
    def add_entity_link(self, obj):
        """ optional function
        If the data of the object has an entity_links list this function 
        will get called with each entity"""
        pass

    ########
    # HELPER FUNCTIONS 
    # NOT EXPECTING TO NEED TO BE OVERRIDDEN
    ########
    def _is_entry_match(self, match_entries: dict, rvc_msg: dict) -> bool:
        '''
        Determine if a RVC message matches the map_entries.  
        All fields in match_entries must match the same fields in rvc_msg.

        ret True if match
        ret False if no match
        
        '''
        for k,v in match_entries.items():
            if k not in rvc_msg:
                return False
            
            if rvc_msg[k] != v:
                return False
        
        return True

    def set_rvc_send_queue(self, send_queue: queue):
        """ Provide queue for sending RVC messages.  Queue requires 
        items be formatted as python-can messages"""
        self.send_queue: queue = send_queue

    def get_availability_discovery_info_for_ha(self) -> dict:
        """ return the availability fields in dict format"""
        return { "availability_topic": self.mqtt_support.bridge_state_topic }

