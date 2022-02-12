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
import json
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass


class TemperatureSensor_THERMOSTAT_AMBIENT_STATUS(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"type": "temperature", "name": "THERMOSTAT_AMBIENT_STATUS"}

    """ Provide basic temperature values using THERMOSTAT_AMBIENT_STATUS 

    """

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "temperature-1FF9C-i" + str(data["instance"])
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following to be this device
        self.rvc_match_status = {"name": "THERMOSTAT_AMBIENT_STATUS", "instance": data['instance']}
        self.reported_temp = 100  # should never get this hot in C
        self.Logger.debug(f"Must match: {str(self.rvc_match_status)}")

        self.name = data['instance_name']
        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Temperature Sensor from THERMOSTAT_AMBIENT_STATUS"
                       }

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        # For now only match the status message.

        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")
            # These events happen a lot.  Lets filter down to when temp changes
            if new_message["ambient_temp"] != self.reported_temp:
                self.reported_temp = new_message["ambient_temp"]
                self.mqtt_support.client.publish(
                    self.status_topic, self.reported_temp, retain=True)
            return True
        return False

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data    
        """

        # produce the HA MQTT discovery config json
        config = {"name": self.name, "state_topic": self.status_topic,
                  "qos": 1, "retain": False,
                  "unit_of_meas": '°C',
                  "device_class": "temperature",
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
