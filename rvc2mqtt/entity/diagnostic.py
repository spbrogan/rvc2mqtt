"""
Diagnostic

This is Diagnostic Message which can provide status

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
import copy
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass


class Diagnostic(EntityPluginBaseClass):
    FACTORY_MATCH_ATTRIBUTES = {"type": "diagnostic", "name": "DM_RV"}
    ON = "True"
    OFF = "False"

    """ Provide basic diagnostic information from DM_RV

    Floor plan Data needs to be:

    type: diagnostic
    name: DM_RV
    instance_name: <friendly name>
    source_id: '<source_id>'


    HA mqtt discovery is:
        sensor/<uid>/power_state/config
        binary_sensor/<uid>/warning/config
             with attributes that include the full record
        binary_sensor/<uid>/fault/config
            with attributes that include the full record
        sensor/<uid>/warning_message/config
        sensor/<uid>fault_message/config

    """

    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = "diagnostic-s" + str(data["source_id"])
        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following to be this device
        self.rvc_match_status = {"name": "DM_RV", "source_id": data['source_id']}
        self.Logger.debug(f"Must match: {str(self.rvc_match_status)}")

        # make additional topics
        self.warning_status_topic = mqtt_support.make_device_topic_string(
            self.id, "warning", True)
        self.warning_attributes_topic = mqtt_support.make_device_topic_string(
            self.id, "warning_attributes", True)
        self.warning_msg_topic = mqtt_support.make_device_topic_string(
            self.id, "warning_message", True)
        self.fault_status_topic = mqtt_support.make_device_topic_string(
            self.id, "fault", True)
        self.fault_attributes_topic = mqtt_support.make_device_topic_string(
            self.id, "fault_attributes", True)
        self.fault_msg_topic = mqtt_support.make_device_topic_string(
            self.id, "fault_message", True)
        

        # init members of the class
        self.name = data['instance_name']
        self.source_id = data['source_id']
        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Diagnostic Endpoint from DM_RV"
                       }
        self.warning_attributes = {}
        self.warning_msg = ""
        self.fault_attributes = {}
        self.fault_msg = ""
        self._fault = False
        self._warning = False
        self._state = "unknown"
        self._changed = True

    #### Try using properties so that change tracking can be easier
    #### This might be overly complex and be an over optimization
    #### Does python have something better for this tracking.

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value != self._state:
            self._state = value
            self._changed = True

    @property
    def fault(self):
        return self._fault

    @fault.setter
    def fault(self, value):
        if value != self._fault:
            self._fault = value
            self._changed = True
        
    @property
    def warning(self):
        return self._fault

    @warning.setter
    def warning(self, value):
        if value != self._warning:
            self._warning = value
            self._changed = True

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False
        """
        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")

            self.fault = new_message["red_lamp_status"] != '00'
            self.fault_msg = f"Failure Mode Identifier: {new_message['fmi']} - {new_message['fmi_definition']}" 
            self.fault_attributes = new_message

            self.warning = new_message["yellow_lamp_status"] != '00'
            self.warning_msg = f"Failure Mode Identifier: {new_message['fmi']} - {new_message['fmi_definition']}" 
            self.warning_attributes = new_message
            
            self.state = new_message["operating_status_definition"]

            self._update_mqtt_topics_with_changed_values()
            return True
        return False


    def _update_mqtt_topics_with_changed_values(self):
        if self._changed:            
            self.mqtt_support.client.publish(
                self.status_topic, self.state, retain=True)

            self.mqtt_support.client.publish(
                self.warning_status_topic, self.warning, retain=True)

            self.mqtt_support.client.publish(
                self.warning_msg_topic, self.warning_msg, retain=True)

            self.mqtt_support.client.publish(
                self.warning_attributes_topic, json.dumps(self.warning_attributes), retain=True)

            self.mqtt_support.client.publish(
                self.fault_status_topic, self.fault, retain=True)

            self.mqtt_support.client.publish(
                self.fault_msg_topic, self.fault_msg, retain=True)

            self.mqtt_support.client.publish(
                self.fault_attributes_topic, json.dumps(self.fault_attributes), retain=True)
            
            self._changed = False


    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data    
        """

        # produce the HA MQTT discovery config json
        config = {"name": self.name + " power state",
                  "state_topic": self.status_topic,
                  "qos": 1, "retain": False,
                  "unique_id": self.unique_device_id + "_power_state",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())
        config_json = json.dumps(config)
        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(self.unique_device_id, "sensor", "power_state")
        self.mqtt_support.client.publish(ha_config_topic, config_json, retain=True)

        # produce the HA MQTT discovery config json for binary sensor fault
        config = {"name": self.name + " fault state",
                  "state_topic": self.fault_status_topic,
                  "qos": 1, "retain": False,
                  "payload_on": Diagnostic.ON,
                  "payload_off": Diagnostic.OFF,
                  "json_attributes_topic": self.fault_attributes_topic,
                  "unique_id": self.unique_device_id + "_fault_state",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())
        config_json = json.dumps(config)
        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(self.unique_device_id, "binary_sensor", "fault_state")
        self.mqtt_support.client.publish(ha_config_topic, config_json, retain=True)

        # produce the HA MQTT discovery config json for text sensor fault msg
        config = {"name": self.name + " fault message",
                  "state_topic": self.fault_msg_topic,
                  "qos": 1, "retain": False,
                  "unique_id": self.unique_device_id + "_fault_message",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())
        config_json = json.dumps(config)
        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(self.unique_device_id, "sensor", "fault_message")
        self.mqtt_support.client.publish(ha_config_topic, config_json, retain=True)

        # produce the HA MQTT discovery config json for binary sensor warning
        config = {"name": self.name + " warning state",
                  "state_topic": self.warning_status_topic,
                  "qos": 1, "retain": False,
                  "payload_on": Diagnostic.ON,
                  "payload_off": Diagnostic.OFF,
                  "json_attributes_topic": self.warning_attributes_topic,
                  "unique_id": self.unique_device_id + "_warning_state",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())
        config_json = json.dumps(config)
        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(self.unique_device_id, "binary_sensor", "warning_state")
        self.mqtt_support.client.publish(ha_config_topic, config_json, retain=True)

        # produce the HA MQTT discovery config json for text sensor warning msg
        config = {"name": self.name + " warning message",
                  "state_topic": self.warning_msg_topic,
                  "qos": 1, "retain": False,
                  "unique_id": self.unique_device_id + "_warning_message",
                  "device": self.device}
        config.update(self.get_availability_discovery_info_for_ha())
        config_json = json.dumps(config)
        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(self.unique_device_id, "sensor", "warning_message")
        self.mqtt_support.client.publish(ha_config_topic, config_json, retain=True)