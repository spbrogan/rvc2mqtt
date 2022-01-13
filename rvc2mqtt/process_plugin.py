"""
Defines an abstract class that defines an API for a process plugin.

This type of plugin is used to modify an RVC Msg dict. 

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


class IProcessPlugin(object):
    CONFIG_KEY: str = "to_be_filled_in_by_you"

    def __init__(self, config: Optional(dict)):
        pass

    ##
    # Function to process a RVC msg
    #
    def process_rvc_message(self, msg: dict) -> bool:
        pass
