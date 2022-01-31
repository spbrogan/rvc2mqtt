"""
Plugin Management for Entities

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
import sys
import logging

import pkgutil
import importlib
import inspect

from rvc2mqtt.entity import EntityPluginBaseClass

class PluginSupport(object):
   """ This class helps get and load the correct Plugins.

   Data is a dictionary with the following possible content.
   paths:
      - <path 1>
      - <path 2>

   """

   def __init__(self, internal_plugin_path: os.PathLike, optional_paths: list):
      self.Logger = logging.getLogger(__name__)
      self.plugin_locations = [internal_plugin_path]
      for p in optional_paths:
         if os.path.exists(p):
            p = os.path.abspath(p)
            self.Logger.debug(f"Adding Valid Plugin Path: {p}")
            self.plugin_locations.append(p)
         else:
            self.Logger.error(f"Invalid Plugin Path: {p}")
      
   def register_with_factory_the_entity_plugins(self, factory_map:list):
      """
      Load the classes defined in plugins that are:
         * subclass of EntityPluginBaseClass and 
         * define class dict of FACTORY_MATCH_ATTRIBUTES
      Register the class with the factory

      DEVELOPER NOTE:  This is pretty hacky.  This was hacked together
      with trial and error.  I am sure numerous steps are not needed
      or different functions/implementations could be used
         
      """
      # Get all python modules from a given set of paths
      for a in pkgutil.walk_packages(self.plugin_locations):
          # Create a spec from the source file
         spec =  importlib.util.spec_from_file_location(a[1], os.path.join(a[0].path, a[1] + ".py"))
        
         # create a module item from the spec
         module = importlib.util.module_from_spec(spec)

         # add it to the sys.modules cache
         sys.modules[a[0]] = module

         # Execute the module - load?
         spec.loader.exec_module(module)

         # Loop thru the module and find all the classes defined
         for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            # Check if the attribute is a class, and subclass of our plugin base class
            if inspect.isclass(attribute) and issubclass(attribute, EntityPluginBaseClass):
               if "FACTORY_MATCH_ATTRIBUTES" in dir(attribute):
                  fma = getattr(attribute, "FACTORY_MATCH_ATTRIBUTES")
                  factory_map.append((fma, attribute))                  
