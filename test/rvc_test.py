"""
Unit tests for the rvc decoder class

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

class Test_RVC_Decoder(unittest.TestCase):

    def test_rvc_valid_pgn(self):
        
        rvc = RVC_Decoder()
        rvc.load_rvc_spec(rvc_spec_file_path)

        results = rvc.rvc_decode(int("19ffe259", 16), "02000060246024ff")
        print(results)

        # acknowledge
        results = rvc.rvc_decode(int("18E84480", 16), "8001000000BCFF01")
        self.assertEqual('0E844', results['dgn'])
        self.assertEqual('ACKNOWLEDGMENT', results['name'])
        self.assertEqual('command-specific response', results['acknowledgment_code_definition'])

    def test_canbus_to_rvc(self):
        rvc = RVC_Decoder()
        result = rvc._can_frame_to_rvc(int("19FFBC44", 16))
        self.assertEqual('6', result["priority"])
        self.assertEqual('1FF', result["dgn_h"])
        self.assertEqual('BC', result["dgn_l"])
        self.assertEqual('1FFBC', result["dgn"])
        self.assertEqual('44', result["source_id"])

        print(result)

    def test_rvc_to_canbus_round_trip(self):
        rvc = RVC_Decoder()
        result = rvc._can_frame_to_rvc(int("19FFBC44", 16))
        arbid = rvc._rvc_to_can_frame(result)
        self.assertEqual(arbid, 0x19FFBC44)

        result = rvc._can_frame_to_rvc(int("19ffe259", 16))
        arbid = rvc._rvc_to_can_frame(result)
        self.assertEqual(arbid, 0x19ffe259)

    def test_rvc_to_canbus_defaults(self):
        rvc = RVC_Decoder()
        arbitration_id = rvc._rvc_to_can_frame({"dgn": "1FFBC"})
        # Defaults are defined in rvc.py
        # priority default is 0x6
        # source address default is 0x82  
        self.assertEqual(arbitration_id, int("19FFBC82", 16))

    # -------------------
    # Test Byte Function
    # -------------------
    def test_rvc_byte_simple_string(self):
        rvc = RVC_Decoder()
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "0"), "AA")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "1"), "BB")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "2"), "CC")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "3"), "DD")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "4"), "11")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "5"), "22")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "6"), "33")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "7"), "44")

    def test_rvc_byte_simple_int(self):
        rvc = RVC_Decoder()
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 0), "AA")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 1), "BB")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 2), "CC")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 3), "DD")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 4), "11")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 5), "22")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 6), "33")
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", 7), "44")

    def test_rvc_byte_range(self):
        rvc = RVC_Decoder()
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "0-1"), "BBAA")     #2
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "2-3"), "DDCC")     #2
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "5-7"), "443322")   #3
        self.assertEqual(rvc._get_bytes("AABBCCDD11223344", "4-7"), "44332211") #4

    def test_rvc_get_byte_invalid(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bytes("AABBCCDD11223344", "8")
        with self.assertRaises(Exception) as cm:
            rvc._get_bytes("AABBCCDD11223344", "3-8")

    def test_rvc_get_byte_invalid_range_end_before_start(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bytes("AABBCCDD11223344", "4-2")

    def test_rvc_get_byte_invalid_range_string(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bytes("AABBCCDD11223344", "4-8-0")

    # ------------------
    # Test Bit function
    # ------------------
    def test_rvc_bit_simple_int(self):
        rvc = RVC_Decoder()
        self.assertEqual(rvc._get_bits(0x01, 0), "1")
        self.assertEqual(rvc._get_bits(0x02, 1), "1")
        self.assertEqual(rvc._get_bits(0x04, 2), "1")
        self.assertEqual(rvc._get_bits(0x08, 3), "1")
        self.assertEqual(rvc._get_bits(0x10, 4), "1")
        self.assertEqual(rvc._get_bits(0x20, 5), "1")
        self.assertEqual(rvc._get_bits(0x40, 6), "1")
        self.assertEqual(rvc._get_bits(0x80, 7), "1")

        self.assertEqual(rvc._get_bits(0xFE, 0), "0")
        self.assertEqual(rvc._get_bits(0xFD, 1), "0")
        self.assertEqual(rvc._get_bits(0xFB, 2), "0")
        self.assertEqual(rvc._get_bits(0xF7, 3), "0")
        self.assertEqual(rvc._get_bits(0xEF, 4), "0")
        self.assertEqual(rvc._get_bits(0xDF, 5), "0")
        self.assertEqual(rvc._get_bits(0xBF, 6), "0")
        self.assertEqual(rvc._get_bits(0x7F, 7), "0")

    def test_rvc_bit_simple_string(self):
        rvc = RVC_Decoder()
        self.assertEqual(rvc._get_bits(0xFF, "0"), "1")

        self.assertEqual(rvc._get_bits(0x01, "0"), "1")
        self.assertEqual(rvc._get_bits(0x02, "1"), "1")
        self.assertEqual(rvc._get_bits(0x04, "2"), "1")
        self.assertEqual(rvc._get_bits(0x08, "3"), "1")
        self.assertEqual(rvc._get_bits(0x10, "4"), "1")
        self.assertEqual(rvc._get_bits(0x20, "5"), "1")
        self.assertEqual(rvc._get_bits(0x40, "6"), "1")
        self.assertEqual(rvc._get_bits(0x80, "7"), "1")

        self.assertEqual(rvc._get_bits(0xFE, "0"), "0")
        self.assertEqual(rvc._get_bits(0xFD, "1"), "0")
        self.assertEqual(rvc._get_bits(0xFB, "2"), "0")
        self.assertEqual(rvc._get_bits(0xF7, "3"), "0")
        self.assertEqual(rvc._get_bits(0xEF, "4"), "0")
        self.assertEqual(rvc._get_bits(0xDF, "5"), "0")
        self.assertEqual(rvc._get_bits(0xBF, "6"), "0")
        self.assertEqual(rvc._get_bits(0x7F, "7"), "0")

    def test_rvc_bit_range(self):
        rvc = RVC_Decoder()
        #B'1100 1001
        self.assertEqual(rvc._get_bits(0xC9, "0-1"), "01")
        self.assertEqual(rvc._get_bits(0xC9, "1-2"), "00")
        self.assertEqual(rvc._get_bits(0xC9, "2-3"), "10")
        self.assertEqual(rvc._get_bits(0xC9, "3-4"), "01")
        self.assertEqual(rvc._get_bits(0xC9, "4-5"), "00")
        self.assertEqual(rvc._get_bits(0xC9, "5-6"), "10")
        self.assertEqual(rvc._get_bits(0xC9, "6-7"), "11")

    def test_rvc_get_bits_invalid(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bits(0xFF, "8")
        with self.assertRaises(Exception) as cm:
            rvc._get_bits(0x11, "3-8")

    def test_rvc_get_byte_invalid_range_end_before_start(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bits(0x22, "4-2")

    def test_rvc_get_byte_invalid_range_string(self):
        rvc = RVC_Decoder()
        with self.assertRaises(Exception) as cm:
            rvc._get_bits(0xff, "4-8-0")


if __name__ == '__main__':
    unittest.main()
