"""
Unit tests for the hvac entity class

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

import unittest
from unittest.mock import MagicMock
import context  # add rvc2mqtt package to the python path using local reference
from rvc2mqtt.entity.hvac import HvacClass

class Test_HvacClimate(unittest.TestCase):

    def test_basic(self):
        mock = MagicMock()
        mock.mqtt_support.make_device_topic_string.return_value = 'topic_string'
        
        l = HvacClass({'instance': 1, 'instance_name': "test hvac"}, mock)
        self.assertTrue(type(l), HvacClass)

    def test_convert_c_to_uint16(self):
        mock = MagicMock()
        mock.mqtt_support.make_device_topic_string.return_value = 'topic_string'

        l = HvacClass({'instance': 1, 'instance_name': "test hvac"}, mock)
        self.assertEqual(l._convert_temp_c_to_rvc_uint16(17.75), 0x2458)
        self.assertEqual(l._convert_temp_c_to_rvc_uint16(18.00), 0x2460)
        self.assertEqual(l._convert_temp_c_to_rvc_uint16(17.22), 0x2447)
        self.assertEqual(l._convert_temp_c_to_rvc_uint16(15.53), 0x2411)
        self.assertEqual(l._convert_temp_c_to_rvc_uint16(25.53), 0x2551)

    def test_fan_mode(self):

        mock = MagicMock()
        mock.mqtt_support.make_device_topic_string.return_value = 'topic_string'

        l = HvacClass({'instance': 1, 'instance_name': "test hvac"}, mock)
        self.assertEqual(l._convert_fan_mode_and_speed_to_mqtt_fan_mode('on', 25), "low")
        self.assertEqual(l._convert_fan_mode_and_speed_to_mqtt_fan_mode('on', 50), "medium")
        self.assertEqual(l._convert_fan_mode_and_speed_to_mqtt_fan_mode('on', 100), "high")
        self.assertEqual(l._convert_fan_mode_and_speed_to_mqtt_fan_mode('on', 0), "off")
        self.assertEqual(l._convert_fan_mode_and_speed_to_mqtt_fan_mode('auto', 0), "auto") # speed doesn't matter

    def test_mode_conversion(self):
        mock = MagicMock()
        mock.mqtt_support.make_device_topic_string.return_value = 'topic_string'

        l = HvacClass({'instance': 1, 'instance_name': "test hvac"}, mock)
        self.assertEqual(l._convert_mqtt_to_rvc_mode('off'), "off")
        self.assertEqual(l._convert_mqtt_to_rvc_mode('cool'), "cool")
        self.assertEqual(l._convert_mqtt_to_rvc_mode('fan_only'), "fan only")
        self.assertEqual(l._convert_mqtt_to_rvc_mode('heat'), "aux heat")





if __name__ == '__main__':
    unittest.main()
