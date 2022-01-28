"""
entity factory

Make entity objects based on the plugins loaded and the config data supplied

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
from rvc2mqtt.entity import EntityPluginBaseClass
from rvc2mqtt.mqtt import MQTT_Support

def entity_factory(data: dict, mqtt_support: MQTT_Support, entity_factory_list: list) -> EntityPluginBaseClass:
    # loop thru the factory list and if a full match between factory and data then
    # instantiate the object. 
    logger = logging.getLogger(__name__)
    logger.debug(f"Factory for: {str(data)}")
    for f_entry in entity_factory_list:
        match = True
        for k,v in f_entry[0].items():
            if k not in data:
                logger.debug(f"Key not in data: {k}")
                match = False
                break
            if data[k] != v:
                logger.debug(f"Value {v} for key {k} not the same as data: {str(data)}")
                match = False
                break
        # finished or break - check for match
        if match:
            # matched.  Make matching entity
            logger.debug(f"Found Entity Match for {str(data)} as {f_entry[1].__name__}")
            return f_entry[1](data, mqtt_support)
        
    logger.error(f"Unsupported entity: {str(data)}")
    return None
    