"""
HVAC support using Climate MQTT


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
import struct
import json
from enum import Enum
from typing import Union
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass



class FanMode(Enum):
    '''
    simple class for the Fan Mode which includes Fan Modes and speed
    
    '''

    AUTO = 'auto'
    LOW  = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    OFF = 'off'

    @property
    def rvc_fan_speed_percent(self) -> int:
        if self.value == 'auto':
            return 50
        elif self.value == 'low':
            return 25
        elif self.value == 'medium':
            return 50
        elif self.value == 'high':
            return 100
        elif self.value == 'off':
            return 0
        else:
            return 0
    
    @property
    def rvc_fan_speed_for_rvc_msg(self) -> int:
        return self.rvc_fan_speed_percent * 2

    @property
    def rvc_fan_mode_str(self) -> str:
        if self.value == 'auto':
            return 'auto'
        else:
            return 'on'
    
    @property
    def rvc_fan_mode_int(self) -> int:
        if self.value == 'auto':
            return 0
        else:
            return 1

    @staticmethod
    def get_fan_mode_from_rvc(speed: int, rvc_mode:str):
        if rvc_mode == 'auto':
            return FanMode.AUTO
        elif speed == 0:
            return FanMode.OFF
        elif speed == 25:
            return FanMode.LOW
        elif speed == 50:
            return FanMode.MEDIUM
        elif speed == 100:
            return FanMode.HIGH
    
class HvacMode(Enum):
    '''
    simple class for the HVAC Mode which includes heat, cool, etc
    
    '''
    OFF = 'off'
    COOL = 'cool'
    FAN_ONLY = 'fan_only'
    HEAT = 'heat'

    @property
    def rvc_mode_for_rvc_msg(self) -> str:
        if self == HvacMode.HEAT:
            return 5
        elif self == HvacMode.FAN_ONLY:
            return 4
        elif self == HvacMode.COOL:
            return 1
        elif self == HvacMode.OFF:
            return 0
    
    @staticmethod
    def get_hvac_mode_from_rvc(rvc_mode:str):
        if rvc_mode == 'aux heat':
            return HvacMode.HEAT
        elif rvc_mode == "fan only":
            return HvacMode.FAN_ONLY
        else:
            return HvacMode(rvc_mode)


class HvacClass(EntityPluginBaseClass):
    '''
    HVAC based on climate control based on THERMOSTAT_STATUS_1 and optional temperature entities
    DGNs

    This is a multi instance device
    FLOORPLAN - Input

    type: hvac
    name: THERMOSTAT_STATUS_1
    instance_name: <friendly name>
    instance: <int>
    link_id: <str for this node> (optional, only used for linking)
    entity_links:
      - <link id of associated current temp sensor>




    HA Autodiscovery
    https://www.home-assistant.io/integrations/climate.mqtt/
        hvac
          current_temperature_topic
          current_temperature_template 

          fan_mode_command_template
          fan_mode_command_topic 
          fan_mode_state_template 
          fan_mode_state_topic 
          fan_modes 

          max_temp 
          min_temp 

          mode_command_template 
          mode_command_topic 
          mode_state_template 
          mode_state_topic 
          modes    
    ''' 

    FACTORY_MATCH_ATTRIBUTES = {"name": "THERMOSTAT_STATUS_1", "type": "hvac"}

    # HA MQTT HVAC supported modes - must be a subset of default
    MQTT_SUPPORTED_MODES = [e.value for e in HvacMode]

    MIN_TEMP = 12
    MAX_TEMP = 30

    # HA MQTT FAN supported modes - must be subset of default
    #MQTT_SUPPORTED_FAN_MODE = ["auto", "low", "medium", "high"]
    MQTT_SUPPORTED_FAN_MODE =  [e.value for e in FanMode]

    # convert rvc friendly name to rvc value
    RVC_SCHEDULE_MODE_TO_RVC_SCHEDULE_MODE_VALUE = {"disabled": 0, "enabled": 1}


    def __init__(self, data: dict, mqtt_support: MQTT_Support):
        self.id = f"thermostat-i" + str(data["instance"])

        super().__init__(data, mqtt_support)
        self.Logger = logging.getLogger(__class__.__name__)

        # RVC message must match the following status or command
        self.rvc_match_status = {"name": "THERMOSTAT_STATUS_1", "instance": data['instance']}
        self.rvc_match_command = {"name": "THERMOSTAT_COMMAND_1", "instance": data['instance']}

        self.Logger.debug(f"Must match: {str(self.rvc_match_status)} {str(self.rvc_match_command)}")

        self.temperature_entity_link = None
        
        # fields for a thermostat object
        self.name = data["instance_name"]
        self.rvc_instance = data["instance"]
        self.scheduled_mode = "disabled"  # don't support this

        self._mode     = HvacMode.OFF
        self._fan_mode = FanMode.OFF


        self._set_point_temperature = 16.09

        self.device = {"manufacturer": "RV-C",
                       "via_device": self.mqtt_support.get_bridge_ha_name(),
                       "identifiers": self.unique_device_id,
                       "name": self.name,
                       "model": "RV-C Thermostat from THERMOSTAT_STATUS_1"
                       }

        # Allow MQTT to control mode
        self.status_mode_topic = mqtt_support.make_device_topic_string(self.id, "mode", True)
        self.command_mode_topic = mqtt_support.make_device_topic_string(self.id, "mode", False)
        self.mqtt_support.register(self.command_mode_topic, self.process_mqtt_msg)

        # Allow MQTT to control fan mode
        self.status_fan_mode_topic = mqtt_support.make_device_topic_string(self.id, "fan_mode", True)
        self.command_fan_mode_topic = mqtt_support.make_device_topic_string(self.id, "fan_mode", False)
        self.mqtt_support.register(self.command_fan_mode_topic, self.process_mqtt_msg)

        # Allow MQTT to control the target temperature
        self.status_set_point_temp_topic = mqtt_support.make_device_topic_string(self.id, "set_point_temperature", True)
        self.command_set_point_temp_topic = mqtt_support.make_device_topic_string(self.id, "set_point_temperature", False)
        self.mqtt_support.register(self.command_set_point_temp_topic, self.process_mqtt_msg)

    @property
    def fan_mode(self) -> FanMode:
        return self._fan_mode

    @fan_mode.setter
    def fan_mode(self, value: FanMode):
        if value != self._fan_mode:
            self._fan_mode = value
            self._changed = True

    @property
    def mode(self) -> HvacMode:
        return self._mode

    @mode.setter
    def mode(self, value: HvacMode):
        if value != self._mode:
            self._mode = value
            self._changed = True


    @property
    def set_point_temperature(self) -> float:
        return self._set_point_temperature

    @set_point_temperature.setter
    def set_point_temperature(self, value: float):
        if value != self._set_point_temperature:
            self._set_point_temperature = value
            self._changed = True
    


    def add_entity_link(self, obj):
        """ optional function
        If the data of the object has an entity_links list this function 
        will get called with each entity"""
        
        self.temperature_entity_link = obj

    def process_rvc_msg(self, new_message: dict) -> bool:
        """ Process an incoming message and determine if it
        is of interest to this object.

        If relevant - Process the message and return True
        else - return False

        Message looks like:

        
            RV-C message for THERMOSTAT_STATUS_1

        {'arbitration_id': '0x19ffe259', 'data': '02000060246024FF', 'priority': '6', 'dgn_h': '1FF', 'dgn_l': 'E2', 'dgn': '1FFE2',
            'source_id': '59', 'name': 'THERMOSTAT_STATUS_1', 'instance': 2,
            'operating_mode': '0000', 'operating_mode_definition': False,
            'fan_mode': '00', 'fan_mode_definition': 'auto',
            'schedule_mode': '00', 'schedule_mode_definition': 'disabled',
            'fan_speed': 0.0,
            'setpoint_temp_heat': 18.0,
            'setpoint_temp_cool': 18.0}

        """


        if self._is_entry_match(self.rvc_match_status, new_message):
            self.Logger.debug(f"Msg Match Status: {str(new_message)}")

            self.fan_mode = FanMode.get_fan_mode_from_rvc(int(new_message["fan_speed"]), new_message["fan_mode_definition"] )
            # use cool because for this implementation we will update cool and heat to the same value
            self.set_point_temperature = new_message["setpoint_temp_cool"]
            if new_message["setpoint_temp_cool"] != new_message["setpoint_temp_heat"]:
                self.Logger.error(f"Expected cool and heat set temperatures to always be the same.  They are not")
            self.mode = HvacMode.get_hvac_mode_from_rvc(new_message["operating_mode_definition"])
            self._update_mqtt_topics_with_changed_values()
            return True
        elif self._is_entry_match(self.rvc_match_command, new_message):
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            # do nothing from command
        return False

    def _update_mqtt_topics_with_changed_values(self):
        ''' entry data has potentially changed.  Update mqtt'''

        if self._changed: 

            self.mqtt_support.client.publish(
                self.status_mode_topic, self.mode.value, retain=True
            )

            self.mqtt_support.client.publish(self.status_fan_mode_topic, self.fan_mode.value, retain=True)
            self.mqtt_support.client.publish(self.status_set_point_temp_topic, self.set_point_temperature, retain=True)
            self._changed = False
        return False

    def _convert_temp_c_to_rvc_uint16(self, temp_c: float):
        ''' convert a temperature stored in C to a UINT16 value for RVC'''
        return round((temp_c + 273 ) * 32)


    def _make_rvc_payload(self, instance:int, mode:HvacMode, fan_mode:FanMode, schedule_mode:str, temperature_c:float):
        ''' Make 8 byte buffer in THERMOSTAT_COMMAND_1 format. 
        
        {   'arbitration_id': '0x19fef944', 'data': '0200645824582400',
            'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9',
            'source_id': '44',
            'name': 'THERMOSTAT_COMMAND_1',
            'instance': 2,
            'operating_mode': '0000', 'operating_mode_definition': 'off',
            'fan_mode': '00', 'fan_mode_definition': 'auto',
            'schedule_mode': '00', 'schedule_mode_definition': 'disabled',
            'fan_speed': 50.0, 
            'setpoint_temp_heat': 17.75, 'setpoint_temp_cool': 17.75}
         '''
        msg_bytes = bytearray(8)
        mi = mode.rvc_mode_for_rvc_msg
        fmi = fan_mode.rvc_fan_mode_int
        smi = HvacClass.RVC_SCHEDULE_MODE_TO_RVC_SCHEDULE_MODE_VALUE[schedule_mode]  # schedule mode int value
        fsi = fan_mode.rvc_fan_speed_for_rvc_msg
        temperature_uint16 = self._convert_temp_c_to_rvc_uint16(temperature_c)

        struct.pack_into("<BBBHHB", msg_bytes, 0, instance, (mi | (fmi << 4) | (smi << 6)), fsi, temperature_uint16, temperature_uint16, 0  )
        return msg_bytes
        

    def process_mqtt_msg(self, topic, payload):
        """ Read mqtt incoming command message

            convert the new value into entity format
            make an rvc command message with the new value 
            queue it
               
        """
        self.Logger.debug(f"MQTT Msg Received on topic {topic} with payload {payload}")

        if topic == self.command_mode_topic:
            try:
                mode = HvacMode(payload.lower())
                pl = self._make_rvc_payload(self.rvc_instance, mode, self.fan_mode, self.scheduled_mode, self.set_point_temperature)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except Exception as e:
                self.Logger.error(f"Exception trying to respond to topic {topic} + {str(e)}")

        elif topic == self.command_fan_mode_topic:
            try: 
                fan_mode = FanMode(payload)
                pl = self._make_rvc_payload(self.rvc_instance, self.mode, fan_mode, self.scheduled_mode, self.set_point_temperature)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except Exception as e:
                self.Logger.error(f"Exception trying to respond to topic {topic} + {str(e)}")

        elif topic == self.command_set_point_temp_topic:
            try: 
                temp = float(payload)
                pl = self._make_rvc_payload(self.rvc_instance, self.mode, self.fan_mode, self.scheduled_mode, temp)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except Exception as e:
                self.Logger.error(f"Exception trying to respond to topic {topic} + {str(e)}")
               
        else:
            self.Logger.error(f"Invalid payload {payload} for topic {topic}")

    def initialize(self):
        """ Optional function 
        Will get called once when the object is loaded.  
        RVC canbus tx queue is available
        mqtt client is ready.  

        This can be a good place to request data

        """
        config = {"name": self.name,
                  "modes": HvacClass.MQTT_SUPPORTED_MODES,
                  "mode_state_topic": self.status_mode_topic,
                  "mode_state_template": '{{value}}',
                  "mode_command_topic": self.command_mode_topic,
                  "mode_command_template": '{{value}}',

                  "temperature_unit": 'C',
                  "min_temp": HvacClass.MIN_TEMP,
                  "max_temp": HvacClass.MAX_TEMP,

                  "fan_modes": HvacClass.MQTT_SUPPORTED_FAN_MODE,
                  "fan_mode_state_topic": self.status_fan_mode_topic,
                  "fan_mode_state_template": '{{value}}',
                  "fan_mode_command_topic": self.command_fan_mode_topic,
                  "fan_mode_command_template": '{{value}}',

                  "temperature_state_topic": self.status_set_point_temp_topic,
                  "temperature_state_template": '{{value}}',
                  "temperature_command_topic": self.command_set_point_temp_topic,
                  "temperature_command_template": '{{value}}',
                  
                  "qos": 1, "retain": False,
                  "unique_id": self.unique_device_id,
                  "device": self.device}

        if self.temperature_entity_link is not None:
            config["current_temperature_topic"] = self.temperature_entity_link.status_topic
            config["current_temperature_template"] = '{{value}}'

        config.update(self.get_availability_discovery_info_for_ha())

        config_json = json.dumps(config)

        ha_config_topic = self.mqtt_support.make_ha_auto_discovery_config_topic(
            self.unique_device_id, "climate")

        # publish info to mqtt
        self.mqtt_support.client.publish(
            ha_config_topic, config_json, retain=True)


'''
RVC functional behavior seen in 2021 Keystone Cougar 28bhswe


rvc turn fan on high

operating mode = fan only
fan mode = on
fan speed = 100.0  

rvc turn fan on low

operating mode = fan only
fan mode = on
fan speed = 25.0


turn mode to cool
2022-03-11 07:54:20 Msg {'arbitration_id': '0x19fef944', 'data': '0101645125512500', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 1, 'operating_mode': '0001', 'operating_mode_definition': 'cool', 'fan_mode': '00', 'fan_mode_definition': 'auto', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 50.0, 'setpoint_temp_heat': 25.53, 'setpoint_temp_cool': 25.53}
2022-03-11 07:54:20 Msg {'arbitration_id': '0x19fea644', 'data': '01150040FFFF5125', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'A6', 'dgn': '1FEA6', 'source_id': '44', 'name': 'ROOF_FAN_COMMAND_1', 'instance': 1, 'system_status': '01', 'system_status_definition': 'on', 'fan_mode': '01', 'fan_mode_definition': 'force on', 'speed_mode': '01', 'speed_mode_definition': 'manual', 'light': '00', 'light_definition': 'off', 'fan_speed_setting': 0.0, 'wind_direction_setting': '00', 'wind_direction_setting_definition': 'air out', 'dome_position': '0000', 'dome_position_definition': 'close', 'rain_sensor': '01', 'ambient_temperature': 'n/a', 'set_point': 25.53}

Turn mode off
2022-03-11 08:01:29 Msg {'arbitration_id': '0x19fef944', 'data': '0100005125512500', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 1, 'operating_mode': '0000', 'operating_mode_definition': 'off', 'fan_mode': '00', 'fan_mode_definition': 'auto', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 0.0, 'setpoint_temp_heat': 25.53, 'setpoint_temp_cool': 25.53}


Turning heat on @ 60f with fan set to auto
2022-03-11 08:07:29 Msg {'arbitration_id': '0x19fef944', 'data': '0205641124112400', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 2, 'operating_mode': '0101', 'fan_mode': '00', 'fan_mode_definition': 'auto', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 50.0, 'setpoint_temp_heat': 15.53, 'setpoint_temp_cool': 15.53}

With heat on at 60f set fan to off
2022-03-11 08:11:19 Msg {'arbitration_id': '0x19fef944', 'data': '0215001124112400', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 2, 'operating_mode': '0101', 'fan_mode': '01', 'fan_mode_definition': 'on', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 0.0, 'setpoint_temp_heat': 15.53, 'setpoint_temp_cool': 15.53}

change heat set point to 63F
2022-03-11 08:15:41 Msg {'arbitration_id': '0x19fef944', 'data': '0215004724472400', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 2, 'operating_mode': '0101', 'fan_mode': '01', 'fan_mode_definition': 'on', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 0.0, 'setpoint_temp_heat': 17.22, 'setpoint_temp_cool': 17.22}

change fan mode to auto
2022-03-11 08:17:40 Msg {'arbitration_id': '0x19fef944', 'data': '0205644724472400', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 2, 'operating_mode': '0101', 'fan_mode': '00', 'fan_mode_definition': 'auto', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 50.0, 'setpoint_temp_heat': 17.22, 'setpoint_temp_cool': 17.22}


change fan mode to Low
2022-03-11 08:18:21 Msg {'arbitration_id': '0x19fef944', 'data': '0215324724472400', 'priority': '6', 'dgn_h': '1FE', 'dgn_l': 'F9', 'dgn': '1FEF9', 'source_id': '44', 'name': 'THERMOSTAT_COMMAND_1', 'instance': 2, 'operating_mode': '0101', 'fan_mode': '01', 'fan_mode_definition': 'on', 'schedule_mode': '00', 'schedule_mode_definition': 'disabled', 'fan_speed': 25.0, 'setpoint_temp_heat': 17.22, 'setpoint_temp_cool': 17.22}

'''