"""
Simple mapping plugin that allows adding a friendly name to a given message

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

from typing import Optional


class SimpleMapPlugin(object):
    CONFIG_KEY: str = "simple_map"

    MAIN_KEY: str = "map"
    ADD_KEY: str = "add"


    def __init__(self, config: Optional[dict]):
        self.map = []
        if self.MAIN_KEY in config:
            for entry in config[self.MAIN_KEY]:
                self.map.append(entry)
        
    def _is_entry_match(self, msg: dict, map_entry: dict) -> bool:
        '''
        Determine if message matches the map_entry.  
        All fields in map_entry must match the same fields in msg.

        ret True if match
        ret False if no match
        
        '''
        for k,v in map_entry.items():
            if k == self.ADD_KEY:
                continue

            if msg[k] != v:
                return False
        
        return True

    def process_rvc_message(self, msg: dict) -> bool:
        '''
        Process a RV-C message

        If a match is found then add the additional keys

        '''
        for entry in self.map:
            if self._is_entry_match(msg, entry):
                for k,v in entry[self.ADD_KEY].items():
                    msg[k] = v
                return True
        return False
