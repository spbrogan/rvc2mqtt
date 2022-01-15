"""
Unit tests for the entity and factory

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
import context  # add rvc2mqtt package to the python path using local reference
import rvc2mqtt.entity

class Test_Entity(unittest.TestCase):

    def test_factory_success(self):

        d = {"type": "Light"}
        obj = rvc2mqtt.entity.entity_factory(d)
        self.assertIsNotNone(obj)
        self.assertTrue(type(obj), rvc2mqtt.entity.Light)

    def test_factory_invalid(self):
        d = {"type": "not_here"}
        obj = rvc2mqtt.entity.entity_factory(d)
        self.assertIsNone(obj)

if __name__ == '__main__':
    unittest.main()
