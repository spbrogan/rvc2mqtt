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
from typing import Union
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.entity import EntityPluginBaseClass

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
    MQTT_SUPPORTED_MODES = ["off", "cool", "heat", "fan_only"]

    # use this to convert the incoming rvc message decoded to mqtt values
    RVC_MODE_TO_MQTT_MODE = {'off': 'off', 'cool': 'cool', 'fan only': 'fan_only', 'aux heat': 'heat' }

    RVC_MODE_TO_RVC_MODE_VALUE = {'off': 0, 'cool': 1, 'fan only': 4, 'aux_heat': 5}

    MIN_TEMP = 12
    MAX_TEMP = 30

    # HA MQTT FAN supported modes - must be subset of default
    MQTT_SUPPORTED_FAN_MODE = ["auto", "low", "medium", "high"]

    # use this to convert mqtt requests to rvc values
    MQTT_TO_RVC_FAN_MODE = {"auto": 'auto', "low": 'on', "medium": 'on', "high": 'on', "off": 'on'}
    MQTT_TO_RVC_FAN_SPEED_VALUE = {"auto": 50, "low": 25, "medium": 50, "high": 100, "off": 0}

    # convert rvc friendly name to rvc value
    RVC_FAN_MODE_TO_RVC_FAN_MODE_VALUE = {"auto": 0, "on": 1}

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

        self._mode     = "unknown"
        self._fan_mode = "unknown"
        self._fan_speed = 0

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
    def fan_mode(self) -> str:
        return self._fan_mode

    @fan_mode.setter
    def fan_mode(self, value: str):
        if value != self._fan_mode:
            self._fan_mode = value
            self._changed = True

    @property
    def fan_speed(self) -> int:
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, value: int):
        if value != self._fan_speed:
            self._fan_speed = value
            self._changed = True

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
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

            self.fan_mode = new_message["fan_mode_definition"]
            self.fan_speed = int(new_message["fan_speed"])
            # use cool because for this implementation we will update cool and heat to the same value
            self.set_point_temperature = new_message["setpoint_temp_cool"]
            if new_message["setpoint_temp_cool"] != new_message["setpoint_temp_heat"]:
                self.Logger.error(f"Expected cool and heat set temperatures to always be the same.  They are not")
            self.mode = new_message["operating_mode_definition"]
            self._update_mqtt_topics_with_changed_values()
            return True
        elif self._is_entry_match(self.rvc_match_command, new_message):
            self.Logger.debug(f"Msg Match Command: {str(new_message)}")
            # do nothing from command
        return False

    def _convert_fan_mode_and_speed_to_mqtt_fan_mode(self, mode:str, speed: int) -> str:
        """ internally this entity stores fan modes as a mode and speed.  MQTT expects
        a different scheme of modes"""
        mqtt_fan_mode = "unknown"
        if mode == "auto":
            mqtt_fan_mode = "auto"
        else:
            for k,v in HvacClass.MQTT_TO_RVC_FAN_SPEED_VALUE.items():
                if k == "auto":
                    continue
                if v == speed:
                    mqtt_fan_mode = k
        return mqtt_fan_mode

    def _update_mqtt_topics_with_changed_values(self):
        ''' entry data has potentially changed.  Update mqtt'''

        if self._changed: 

            self.mqtt_support.client.publish(
                self.status_mode_topic, HvacClass.RVC_MODE_TO_MQTT_MODE[self.mode], retain=True
            )

            mqtt_fan_mode = self._convert_fan_mode_and_speed_to_mqtt_fan_mode(self.fan_mode, self.fan_speed)
            self.mqtt_support.client.publish(self.status_fan_mode_topic, mqtt_fan_mode, retain=True)
            self.mqtt_support.client.publish(self.status_set_point_temp_topic, self.set_point_temperature, retain=True)
            self._changed = False
        return False

    def _convert_temp_c_to_rvc_uint16(self, temp_c: float):
        ''' convert a temperature stored in C to a UINT16 value for RVC'''
        return round((temp_c + 273 ) * 32)


    def _make_rvc_payload(self, instance:int, mode:str, fan_mode:str, schedule_mode:str, rvc_fan_speed:Union[int, float], temperature_c:float):
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
        mi = HvacClass.RVC_MODE_TO_RVC_MODE_VALUE[mode]  # mode int value
        fmi = HvacClass.RVC_FAN_MODE_TO_RVC_FAN_MODE_VALUE[fan_mode]  # fan mode int value
        smi = HvacClass.RVC_SCHEDULE_MODE_TO_RVC_SCHEDULE_MODE_VALUE[schedule_mode]  # schedule mode int value
        fsi = int(rvc_fan_speed) * 2
        temperature_uint16 = self._convert_temp_c_to_rvc_uint16(temperature_c)

        struct.pack_into("<BBBHHB", msg_bytes, 0, instance, (mi | (fmi << 4) | (smi << 6)), fsi, temperature_uint16, temperature_uint16, 0  )
        return msg_bytes

    def _convert_mqtt_to_rvc_mode(self, mqtt_mode):
        ''' Mode values in mqtt need to translated into the format that the 
        entity uses which is a match for the RVC spec.
        '''
        for k,v in HvacClass.RVC_MODE_TO_MQTT_MODE.items():
            if mqtt_mode == v:
                return k
        

    def process_mqtt_msg(self, topic, payload):
        """ Read mqtt incoming command message

            convert the new value into entity format
            make an rvc command message with the new value 
            queue it
               
        """
        self.Logger.debug(f"MQTT Msg Received on topic {topic} with payload {payload}")

        if topic == self.command_mode_topic:
            try:
                mode = self._convert_mqtt_to_rvc_mode(payload.lower())
                pl = self._make_rvc_payload(self.rvc_instance, mode, self.fan_mode, self.scheduled_mode, self.fan_speed, self.set_point_temperature)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except:
                self.Logger.error(f"Exception trying to respond to topic {topic}")

        elif topic == self.command_fan_mode_topic:
            try: 
                fan_mode = HvacClass.MQTT_TO_RVC_FAN_MODE[payload]
                fan_speed = HvacClass.MQTT_TO_RVC_FAN_SPEED_VALUE[payload]
                pl = self._make_rvc_payload(self.rvc_instance, self.mode, fan_mode, self.scheduled_mode, fan_speed, self.set_point_temperature)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except:
                self.Logger.error(f"Exception trying to respond to topic {topic}")

        elif topic == self.command_set_point_temp_topic:
            try: 
                temp = self._convert_temp_c_to_rvc_uint16(payload)
                pl = self._make_rvc_payload(self.rvc_instance, self.mode, self.fan_mode, self.scheduled_mode, self.fan_speed, temp)
                self.send_queue.put({"dgn": "1FEF9", "data": pl})
            except:
                self.Logger.error(f"Exception trying to respond to topic {topic}")
               
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