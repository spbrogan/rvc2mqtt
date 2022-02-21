"""
Tank Level Sensor

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
import json
import struct
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass

class TankLevelSensor_TANK_STATUS(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"type": "tank_level", "name": "TANK_STATUS"}

    """ Provide basic tank level values using DGN TANK_STATUS

    """

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "tanklevel-1FFB7-i" + str(data["instance"])
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following to be this device
        self.rvc_match_status = {"name": "TANK_STATUS", "instance": data['instance']}
        self.level = 100
        self.Logger.debug(f"Must match: {str(self.rvc_match_status)}")

        self.name = data['instance_name']
        self.instance = data['instance']
        self.instance_name = self._get_instance_name(self.instance)

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Tank from TANK_STATUS"
                       }

        self.waiting_for_first_msg = True



    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        # For now only match the status message.

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")

            if(self.waiting_for_first_msg):
                # because we don't have all info until first message we need to wait
                # figure out level resolution
                self.resolution = new_message['resolution']
                # send auto discovery info
                self._send_ha_mqtt_discovery_info()
                # mark first msg sent
                self.waiting_for_first_msg = False

            
            new_level = (new_message["relative_level"] * 100) / self.resolution
            new_level = round(new_level)  # round it..partial precentage isn't important here
            if new_level != self.level:
                self.level = new_level
                self.mqtt_support.client.publish(
                    self.status_topic, self.level, retain=True)
            return True
        return False

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data    
        """
        # request dgn report - this should trigger the tanks to report
        # dgn = 1FFB7 which is actually  BD FF 01 <instance> 00 00 00 00
        self.Logger.debug("Sending Request for DGN")
        data = struct.pack("<BBBBBBBB", int("0xB7", 0), int(
            "0xFF", 0), 1, self.instance, 0, 0, 0, 0)
        self.send_queue.put({"dgn": "EAFF", "data": data})

    
    def _send_ha_mqtt_discovery_info(self):

        # produce the HA MQTT discovery config json
        config = {"name": self.name,
                  "state_topic": self.status_topic,
                  "qos": 1, "retain": False,
                  "unit_of_meas": 'percentage',
                  "state_class": "measurement",
                  "value_template": '{{value}}',
                  "unique_id": self.unique_device_id,
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "sensor")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)

    def _get_instance_name(self, instance: int) -> str:
        imap = {0: "fresh water", 
                1: "black waste", 
                2: "gray waste", 
                3: "lpg",
                16: "second fresh water", 
                17: "second black waste", 
                18: "second gray waste", 
                19: "second lpg" }
        if instance in imap:
            return imap[instance]
        else:
            self.Logger.error(f"Unknown instance name for instance {str(instance)}")
            return "unknown tank type"

