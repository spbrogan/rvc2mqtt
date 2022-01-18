"""
Temperature sensor

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
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass


class Temperature_FromDGN_1FF9C(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"type": "Temperature", "dgn": "1FF9C"}
    
    """ Provide basic temperature values using DGN THERMOSTAT_AMBIENT_STATUS
    
    Example rvc msg: 
    {'arbitration_id': '0x19ff9c59', 'data': '02F522FFFFFFFFFF', 'priority': '6',
     'dgn_h': '1FF', 'dgn_l': '9C', 'dgn': '1FF9C', 'source_id': '59',
     'name': 'THERMOSTAT_AMBIENT_STATUS', 
     'instance': 2, 'ambient_temp': 6.66}

    """
    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following to be this device
        self.rvc_match_status = {"dgn": "1FF9C", "instance": data['instance']}
        self.reported_temp = 100  #should never get this hot in C

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        # For now only match the status message.

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug("Msg Match Status")
            # These events happen a lot.  Lets filter down to when temp changes
            if new_message["ambient_temp"] != self.reported_temp:
                self.reported_temp = new_message["ambient_temp"]
                self.mqtt_support.client.publish(self.status_topic, self.reported_temp, retain=True)
            return True
        return False
            

    def process_mqtt_msg(self, topic, payload):
        pass
        #don't register for anything.  Nothing is settable
