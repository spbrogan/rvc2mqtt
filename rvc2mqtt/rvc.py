"""
Defines a RVC Decoder class for decoding RV-C messages.

This decoder uses a YAML formatted document that describes the RV-C specification
and the various data group number (DGN) and data (bit, bytes, and values found
in the data).  This decoder takes a raw dgn and data buffer and converts to a
more friendly dictionary describing the message. 

RVIA: https://www.rvia.org/node/standards-subcommittee-rv-c
RVC:  http://rv-c.com

# DEV NOTES:
- This class does not do CAN bus communication 

Thanks goes to the contributors of https://github.com/linuxkidd/rvc-monitor-py
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
from os import PathLike
import logging
import ruyaml as YAML
from typing import Union, Tuple


class RVC_Decoder(object):
    DEFAULT_PRIORITY: int = '6'
    DEFAULT_SOURCE_ID: int = '82'  # 130 decimal

    def __init__(self):
        """create a decoder object to support decoding can bus messages
        compliant with the RVIA RV-C
        """
        self.Logger = logging.getLogger(__name__)
        self.spec = {}

    def load_rvc_spec(self, filepath: PathLike) -> None:
        """load the rvc specification yaml file so that messages can be decoded"""

        self.Logger.info(f"Loading RVC Spec file {filepath}")
        with open(filepath, "r") as specfile:
            try:
                yaml=YAML.YAML(typ='safe')
                self.spec = yaml.load(specfile)
            except YAML.YAMLError as err:
                self.Logger.error("Yaml Load Error.\n" + err)
                raise (err)

    def rvc_decode(self, can_arbitration_id: int, data: str) -> dict:
        result = {"arbitration_id": hex(can_arbitration_id), "data": data}
        result.update(self._can_frame_to_rvc(can_arbitration_id))
        result["name"] = "UNKNOWN-" + result["dgn"]

        dgn = result["dgn"]
        if dgn not in self.spec:

            # try just the upper half as a few commands match only upper.
            # commands like ACK
            dgn = result["dgn_h"]

            if dgn not in self.spec:
                self.Logger.warning(f"Failed to find DGN {result['dgn']} in loaded specification")
                return result

        decoder = self.spec[dgn]
        result["name"] = decoder["name"]
        params = []
        try:
            # first load parameters from alias if present
            params.extend(self.spec[decoder["alias"]]["parameters"])
        except:
            pass

        try:
            # extend and override params from this entry
            params.extend(decoder["parameters"])
        except:
            pass

        param_count = 0
        for param in params:

            # Get bytes based on byte param and convert into integer
            try:
                mybytes = self._get_bytes(data, param["byte"])
                myvalue = int(mybytes, 16)  # Get the decimal value of the hex bytes
            except:
                # If you get here, it's because the params had more bytes than the data packet.
                # Thus, skip the rest of the processing
                self.Logger.error(
                    f"Invalid decoding {result.get('name')} param: {param.get('name')} data: {data}"
                )
                continue

            # Get bits if needed for param
            try:
                myvalue = self._get_bits(myvalue, param["bit"])
                if param["type"][:4] == "uint":
                    myvalue = int(myvalue, 2)  # convert binary back to int
            except:
                pass

            # convert if type/unit defined
            try:
                myvalue = self._convert_unit(myvalue, param["unit"], param["type"])
            except:
                pass

            result[param["name"]] = myvalue

            try:
                mydef = "undefined"
                mydef = param["values"][int(myvalue)]
                # int(myvalue) is a hack because the spec yaml interprets binary bits
                # as integers instead of binary strings.
                result[param["name"] + " definition"] = mydef

            except:
                pass

            param_count += 1

        if param_count == 0:
            result["DECODER PENDING"] = 1

        presult = {}
        for key in result.keys():
            presult[self._parameterize_string(key)] = result[key]

        return presult

    def _can_frame_to_rvc(self, arbitration_id: int) -> dict:
        """
        Convert Can Bus 29bit arbitration header into RVC format

        RVC specification section 3.2

        """
        CanID = bin(arbitration_id)[2:].zfill(
            29
        )  # make base two string and zfill to 29 bits
        Priority = format(int(CanID[0:3], 2), "01X")
        DgnH = format(int(CanID[4:13], 2), "03X")
        DgnL = format(int(CanID[13:21], 2), "02X")
        Dgn = DgnH + DgnL
        SrcID = format(int(CanID[21:29], 2), "02X")

        return {
            "priority": Priority,
            "dgn_h": DgnH,
            "dgn_l": DgnL,
            "dgn": Dgn,
            "source_id": SrcID,
        }        

    def _get_bytes(self, bytes: str, byte_range: Union[int, str]) -> str:
        """extract/slice the requested bytes from string of hex data.
            Incoming bytes are not checked for length exception will be
            raised if invalid length.

        @param bytes: hex string of bytes.  Expected format is 16 HEX characters.

        @param byte_range: zero based index of bytes.
               range string is in format of #-#
               For a single byte a string in format of # or an integer can be used.
               All values must be in range of 0-7 inclusive

        @ret - Base 16 (hex) encoded value as string

        """
        if isinstance(byte_range, str) and "-" in byte_range:
            (start, _, end) = byte_range.partition("-")
            start = int(start)
            end = int(end)
            if start < 0 or start > 7:
                self.Logger.error(f"Invalid byte_range {byte_range}")
                raise Exception(f"Invalid Start Integer {start}")

            if end < 0 or end > 7 or end <= start:
                self.Logger.error(f"Invalid byte_range {byte_range}")
                raise Exception(f"Invalid End Integer {end}")

            # reverse order of bytes
            return "".join(
                bytes[i : i + 2] for i in range(end * 2, (start - 1) * 2, -2)
            )
        else:
            # only a single byte.  slice it from bytes
            start = int(byte_range)
            if start < 0 or start > 7:
                self.Logger.error(f"Invalid byte_range {byte_range}")
                raise Exception(f"Invalid Integer {start}")

            return bytes[start * 2 : (start + 1) * 2]

    def _get_bits(self, bits: int, bit_range: Union[int, str]) -> str:
        """extract the requested bit_range from bits

        @param bits: unsigned integer 0-255
        @param bit_range: zero based index inclusive range in a string in format of: # or #-#
        # must be in range of 0-7 inclusive

        @ret base 2 (binary) value encoded as string

        """
        if bits < 0 or bits > 256:
            self.Logger.error(f"Invalid input bits.  Out of Range {bits}")
            raise Exception(f"Invalid input bits Integer {bits}")

        binary_string = "{0:08b}".format(bits)
        if isinstance(bit_range, str) and "-" in bit_range:
            (start, _, end) = bit_range.partition("-")
            start = int(start)
            end = int(end)
            if start < 0 or start > 7:
                self.Logger.error(f"Invalid bit {bit_range}")
                raise Exception(f"Invalid Start Integer {start}")

            if end < 0 or end > 7 or end <= start:
                self.Logger.error(f"Invalid bit_range {bit_range}")
                raise Exception(f"Invalid End Integer {end}")

            return binary_string[7 - end : 8 - start]

        else:
            # only a single bit requested
            start = int(bit_range)
            if start < 0 or start > 7:
                self.Logger.error(f"Invalid bit_range {bit_range}")
                raise Exception(f"Invalid Integer {start}")
            return binary_string[7 - start : 8 - start]

    def _parameterize_string(self, input: str) -> str:
        """
        Convert a string to something easier to use as a JSON parameter by
        converting spaces and slashes to underscores, and removing parentheses.
        e.g.: "Manufacturer Code (LSB) in/out" => "manufacturer_code_lsb_in_out"

        """
        return input.translate(input.maketrans(" /", "__", "()")).lower()

    def _convert_unit(self, input_num: int, unit: str, mytype: str):
        """
        See RVC spec table 5.3 for details
        """
        new_value = input_num
        mu = unit.lower()
        if mu == "pct":
            if input_num != 255:
                new_value = input_num / 2

        elif mu == "deg c":
            new_value = "n/a"
            if mytype == "uint8" and input_num != (1 << 8) - 1:
                new_value = input_num - 40
            elif mytype == "uint16" and input_num != (1 << 16) - 1:
                new_value = round((input_num * 0.03125) - 273, 2)

        elif mu == "v":
            new_value = "n/a"
            if mytype == "uint8" and input_num != (1 << 8) - 1:
                new_value = input_num
            elif mytype == "uint16" and input_num != (1 << 16) - 1:
                new_value = round(input_num * 0.05, 2)

        elif mu == "a":
            new_value = "n/a"
            if mytype == "uint8":
                new_value = input_num
            elif mytype == "uint16" and input_num != (1 << 16) - 1:
                new_value = round((input_num * 0.05) - 1600, 2)
            elif mytype == "uint32" and input_num != (1 << 32) - 1:
                new_value = round((input_num * 0.001) - 2000000, 3)

        elif mu == "hz":
            if mytype == "uint16" and input_num != (1 << 16) - 1:
                new_value = round(input_num / 128, 2)

        elif mu == "sec":
            if mytype == "uint8" and input_num > 240 and input_num < 251:
                new_value = ((input_num - 240) + 4) * 60
            elif mytype == "uint16":
                new_value = input_num * 2

        elif mu == "bitmap":
            new_value = "{0:08b}".format(input_num)

        elif mu == "hex":
            new_value = hex(input_num).upper()[2:]

        return new_value

    def rvc_encode():
        pass

    def _rvc_to_can_frame(self, values: dict) -> int:
        """convert rvc dgn, priority, source_id"""
        a = int(values.get("priority", RVC_Decoder.DEFAULT_PRIORITY), 16)
        b = int(values["dgn"], 16)
        c = int(values.get("source_id", RVC_Decoder.DEFAULT_SOURCE_ID), 16)
        arbitration_id = (a & 0x7)
        arbitration_id = (arbitration_id << 18) | (b & 0x1FFFF)
        arbitration_id = (arbitration_id << 8)  | (c & 0xff)
        return arbitration_id

