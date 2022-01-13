"""
Unit tests for the simple_map_plugin

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
from rvc2mqtt.plugin.simple_map_plugin import SimpleMapPlugin
import yaml
import copy

sample = yaml.safe_load('''
map: 
  - dgn: 1FFBC
    instance: 1
    group: 0
    add:
      friendly_name: bedroom light
      test_key: test1
  - dgn: 1FFBC
    instance: 2
    group: 0
    add:
      friendly_name: main light
      test_key: test2
''')

class Test_simple_map(unittest.TestCase):

    def test_basic_addition(self):
        """ test simple map """
        t = SimpleMapPlugin(sample)

        Message = {"dgn": "1FFBC", "instance": 1, "group": 0}
        match = t.process_rvc_message(Message)
        self.assertTrue(match)
        self.assertEqual(Message["dgn"], "1FFBC")
        self.assertEqual(Message["instance"], 1)
        self.assertEqual(Message["group"], 0)
        self.assertEqual(Message["friendly_name"], "bedroom light")
        self.assertEqual(Message["test_key"], "test1")

    def test_basic_addition2(self):
        """ test simple map """
        t = SimpleMapPlugin(sample)

        Message = {"dgn": "1FFBC", "instance": 2, "group": 0}
        match = t.process_rvc_message(Message)
        self.assertTrue(match)
        self.assertEqual(Message["dgn"], "1FFBC")
        self.assertEqual(Message["instance"], 2)
        self.assertEqual(Message["group"], 0)
        self.assertEqual(Message["friendly_name"], "main light")
        self.assertEqual(Message["test_key"], "test2")

    def test_no_match_addition(self):
        """ test simple map that doesn't match """
        t = SimpleMapPlugin(sample)

        Message = {"dgn": "1FFBD", "instance": 1, "group": 0}
        Message_Pre = copy.deepcopy(Message)
        match = t.process_rvc_message(Message)
        self.assertFalse(match)
        self.assertDictEqual(Message, Message_Pre)


if __name__ == '__main__':
    unittest.main()