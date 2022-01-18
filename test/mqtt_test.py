"""
Unit tests for the mqtt support class

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
import os
import unittest
import context  # add rvc2mqtt package to the python path using local reference
from rvc2mqtt.mqtt import *

## can't figure out how to unit test this..probably need to mock...but given this class is tightly coupled with
## paho mqtt not sure how useful....anyway..below is hack to test it with real mqtt server

class device1(object):

    def __init__(self, name: str, mqtt_support:MQTT_Support):
        self.device_topic = mqtt_support.make_device_topic_root(name)
        self.status_topic = mqtt_support.make_device_topic_string(name, None, True)
        self.set_topic = mqtt_support.make_device_topic_string(name, None, False)
        mqtt_support.client.publish(self.status_topic, "unknown", retain=True)
        mqtt_support.register(self, self.set_topic, self.got_message)
        self.mqtt = mqtt_support


    def got_message(self, topic, payload):
        print(f"hello from device1 {topic} --- {payload.decode('utf-8')}")
        self.mqtt.client.publish(self.status_topic, payload, retain=True)


if __name__ == '__main__':
    #unittest.main()

    mqs = MqttInitalize(Test_MQTT_Support.MQTT_BRIDGE_SETTINGS)

    mqs.client.loop_start()

    d1 = device1("try1", mqs)
    mqs.client.publish(d1.set_topic, "here", retain=False)
    import time
    time.sleep(5)
    mqs.shutdown()



