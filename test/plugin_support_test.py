"""
Unit tests for the plugin_support module

This is just a hack to invoke it..not a unit test

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
from rvc2mqtt.plugin_support import PluginSupport

p_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rvc2mqtt', "entity"))

if __name__ == '__main__':
    ps = PluginSupport( p_path, {})
    fm = []
    ps.register_with_factory_the_entity_plugins(fm)  # will be list of tuples (dict of match parameters, class)
    print(fm)