"""
MQTT support for rvc2mqtt

Thanks goes to the contributers of https://github.com/linuxkidd/rvc-monitor-py
This code is derived from parts of https://github.com/linuxkidd/rvc-monitor-py/blob/master/usr/bin/rvc2mqtt.py
which was licensed using Apache-2.0.  No copyright information was present in the above mentioned file but original
content is owned by the authors. 

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
    
    def __init__(self):
        self.Logger = logging.getLogger(__name__)

    def set_client(self, client):
        self.client = client

    def on_connect(self, client, userdata, flags, rc):
        """ callback function for when it has been connected.
        Should subscribe to topics
        """
        self.Logger.info(f"MQTT connected: {mqc.connack_string(rc)}")
        if rc == mqc.CONNACK_ACCEPTED:
            #subscribe to all topics of interest
            #client.subscribe([(mqttTopic + "/transmit/#", 0)])
            pass
        else:
            self.Logger.critical(f"Failed to connect to mqtt broker: {mqc.connack_string(rc)}")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_message(self, client, userdata, msg):
        pass
        #topic=msg.topic[13:]
        #if debug_level:
        #    print("Send CAN ID: "+topic+" Data: "+msg.payload.decode('ascii'))
        #can_tx(devIds[dev],[ commands[msg.payload.decode('ascii')] ])
        
 ## GLOBALS ##       
gMQTTObj:MQTT_Support = None


def on_mqtt_connect(client, userdata, flags, rc):
    gMQTTObj.on_connect(client, userdata, flags, rc)

def on_mqtt_subscribe(client, userdata, mid, granted_qos):
    gMQTTObj.on_subscribe(client, userdata, mid, granted_qos)

def on_mqtt_message(client, userdata, msg):
    gMQTTObj.on_message(client, userdata, msg)

def MqttInitalize(config:dict):
    """ main function to parse config and initialize the 
    mqtt client.
    """
    global gMQTTObj
    gMQTTObj = MQTT_Support()

    (addr, _, port)=config["broker"].partition(":")
    if port is None:
        port = 1883
    
    mqttc = mqc.Client()
    gMQTTObj.set_client(mqttc)
    mqttc.on_connect = on_mqtt_connect
    mqttc.on_subscribe = on_mqtt_subscribe
    mqttc.on_message = on_mqtt_message

    try:
        logging.getLogger(__name__).info(f"Connecting to MQTT broker {addr}:{port}")
        mqttc.connect(addr, port=port)
        return gMQTTObj
    
    except Exception as e:
        logging.getLogger(__name__).error(f"MQTT Broker Connection Failed. {e}")
        return None
    
    

