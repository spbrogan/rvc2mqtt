"""
Unit tests for the tankwarmer entity class

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
from rvc2mqtt.entity.tank_warmer import TankWarmer_DC_LOAD_STATUS

class Test_Waterheater(unittest.TestCase):

    def test_basic(self):
        
        l = TankWarmer_DC_LOAD_STATUS({'instance': 1}, None)
        self.assertTrue(type(l), TankWarmer_DC_LOAD_STATUS)

if __name__ == '__main__':
    unittest.main()
