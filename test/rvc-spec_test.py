"""
Unit tests for the rvc specification

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
from rvc2mqtt.rvc import RVC_Decoder

rvc_spec_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rvc2mqtt', 'rvc-spec.yml'))

class Test_rvc_spec(unittest.TestCase):

    def test_all_keys_should_be_string(self):
        """ test that all top order entries are strings """
        
        rvc = RVC_Decoder()
        rvc.load_rvc_spec(rvc_spec_file_path)
        failed_keys = []
        for key in rvc.spec.keys():
            if not isinstance(key, str):
                print(f"{str(key)} {str(rvc.spec[key])}")
                failed_keys.append(key)
        
        print(f"There are {len(failed_keys)} keys that are not strings")
        self.assertEqual(len(failed_keys), 0)

    def test_no_values_are_booleans(self):
        rvc = RVC_Decoder()
        rvc.load_rvc_spec(rvc_spec_file_path)
        failed = 0
        tested = 0
        for k,v in rvc.spec.items():
            try:
                for item in v.get("parameters", []):
                    for key,value in item.items():
                        try:
                            for attr, field_value in value.items():
                                tested += 1
                                if isinstance(field_value, bool):
                                    print(f"Found a bool field.  {k} -> parameters -> {key} . {attr} == {field_value}")
                                    failed += 1
                                    print(f"{item['name']}")
                        except:
                            continue
            except:
                continue
        
        print(f"There are {failed} attributes that have a class of bool out of {tested} tested")
        self.assertEqual(failed, 0)

    #add more tests here for the rvc spec and yaml decoding


if __name__ == '__main__':
    unittest.main()