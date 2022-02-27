"""
MQTT support for rvc2mqtt

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
import paho.mqtt.client as mqc


class MQTT_Support(object):
    TOPIC_BASE = "rvc2mqtt"
    HA_AUTO_BASE = "homeassistant"
     
    
    def __init__(self, client_id:str):
        self.Logger = logging.getLogger(__name__)
        self.client_id = client_id
        self._connected = False

        self.root_topic = MQTT_Support.TOPIC_BASE + "/" + self.client_id
        self.device_topic_base = self.root_topic + "/d"

        # topic strings
        self.bridge_state_topic = self.root_topic + "/" + "state"
        self.bridge_info_topic = self.root_topic + "/" + "info"

        self.registered_mqtt_devices = {}


    def register(self, topic, func):
        self.registered_mqtt_devices[topic] = func
        if self._connected:
            self.client.subscribe((topic,0))

    def set_client(self, client: mqc):
        self.client = client

    def on_connect(self, client, userdata, flags, rc):
        """ callback function for when it has been connected.
        Should subscribe to topics
        """
        self.Logger.info(f"MQTT connected: {mqc.connack_string(rc)}")
        if rc == mqc.CONNACK_ACCEPTED:
            # publish topic
            self.client.publish(self.bridge_state_topic, "online", retain=True)
            
            self._connected = True
            topic_tuple_list = [(x, 0) for x in self.registered_mqtt_devices.keys()]
            if len(topic_tuple_list) > 0:
                self.client.subscribe(topic_tuple_list)

        else:
            self.Logger.critical(f"Failed to connect to mqtt broker: {mqc.connack_string(rc)}")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_message(self, client, userdata, msg):
        if msg.topic in self.registered_mqtt_devices:
            func = self.registered_mqtt_devices[msg.topic]
            func(msg.topic, msg.payload.decode('utf-8'))
        else:
            self.Logger.warning("Received mqtt message without a device registered '" + str(msg.payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
    
    def on_disconnect(self, client, userdata, msg):
        self.Logger.critical("MQTT disconnected")
        self._connected = False


    def send_bridge_info(self, info:str):
        pass

    def _make_device_topic_root(self, id:str) -> str:
        return self.device_topic_base + "/" + self._prepare_topic_string_node(id)

    def make_device_topic_string(self, id: str, field:str, state:bool) -> str:
        """ make a topic string for a device.  
        It is either a state topic when you just want status
        Or it is a set topic string if you want to do operations
        """

        s = self._make_device_topic_root(id)

        if field is not None:
            s += "/" + self._prepare_topic_string_node(field) 

        if state:
            s += "/state"
        else:
            s += "/set"
        return s

    def make_ha_auto_discovery_config_topic(self, id: str, ha_component: str, sub_type: str = None) -> str:
        """ make a config topic string for a Home Assistant auto discovery config"""
        topic = MQTT_Support.HA_AUTO_BASE + "/" + ha_component + "/" + self._prepare_topic_string_node(id)
        if sub_type is not None:
            topic += "/" + self._prepare_topic_string_node(sub_type)
        return topic + "/config"


    def _prepare_topic_string_node(self, input:str) -> str:
        """ convert the string to a consistant value
        
        lower case
        only alphanumeric

        """
        return input.translate(input.maketrans(" /", "__", "()")).lower()

    def get_bridge_ha_name(self) -> str:
        """ return a string that is used to identify the bridge HA as a device."""
        return self._prepare_topic_string_node(self.root_topic)



    def shutdown(self):
        """ shutdown.  Tell server we are going offline"""
        self.client.publish(self.bridge_state_topic, "offline", retain=True)
        
 ## GLOBALS ##       
gMQTTObj:MQTT_Support = None


def on_mqtt_connect(client, userdata, flags, rc):
    gMQTTObj.on_connect(client, userdata, flags, rc)

def on_mqtt_subscribe(client, userdata, mid, granted_qos):
    gMQTTObj.on_subscribe(client, userdata, mid, granted_qos)

def on_mqtt_message(client, userdata, msg):
    gMQTTObj.on_message(client, userdata, msg)

def on_mqtt_disconnect(client, userdata, msg):
    gMQTTObj.on_disconnect(client, userdata, msg)

def MqttInitalize(host:str, port:str, user:str, password:str, client_id:str):
    """ main function to parse config and initialize the 
    mqtt client.
    """
    global gMQTTObj
    gMQTTObj = MQTT_Support(client_id)

    port = int(port)
    
    mqttc = mqc.Client(client_id=client_id)
    gMQTTObj.set_client(mqttc)
    mqttc.on_connect = on_mqtt_connect
    mqttc.on_subscribe = on_mqtt_subscribe
    mqttc.on_message = on_mqtt_message
    mqttc.on_disconnect = on_mqtt_disconnect
    mqttc.username_pw_set(user, password)
    mqttc.will_set(gMQTTObj.bridge_state_topic, payload="offline", qos=0, retain=True)
    

    try:
        logging.getLogger(__name__).info(f"Connecting to MQTT broker {host}:{port}")
        mqttc.connect(host, port=port)
        return gMQTTObj
    
    except Exception as e:
        logging.getLogger(__name__).error(f"MQTT Broker Connection Failed. {e}")
        return None


