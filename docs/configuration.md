# Configuration

The main idea is that a yaml config file is used as the single parameter for controlling the service


## Example

``` yaml
#
# define the name of the can device
#
interface:
  name: can0

#
# Logging info
# See https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
#
logger:
  version: 1
  handlers:
    debug_console_handler:
      level: INFO
      class: logging.StreamHandler
      formatter: brief
      stream: ext://sys.stdout
    debug_file_handler:
      level: DEBUG
      class: logging.FileHandler
      formatter: default
      filename: rvc_debug.log
      mode: w
    unhandled_file_handler:
      level: DEBUG
      class: logging.FileHandler
      formatter: time-only
      filename: unhandled_rvc.log
      mode: w
  loggers: 
    '': # root logger
      handlers: 
        - debug_console_handler
        - debug_file_handler
      level: DEBUG
      propagate: False
    'unhandled_rvc':  # special logger for messages not handled
      handlers:
        - unhandled_file_handler
      level: DEBUG
      propagate: False
  formatters:
    brief:
      format: '%(message)s'
    time-only:
      format: '%(asctime)s   %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
    default:
      format: '%(asctime)s %(levelname)-8s %(name)-15s %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'

#
# External Plugins for device entity
#
plugins:
  paths:
    - /home/pi/config
#    - <put folder path here for directory of any plugin's you author>

#
# RV - floor plan
# This is a list of which devices are in your RV
#
# name: must be unique
map: 
  - dgn: 1FFBD
    instance: 1
    group: '00000000'
    type: light
    name: bedroom_light
  - dgn: 1FFBD
    instance: 2
    group: '00000000'
    type: light
    name: main_light
  - dgn: 1FF9C
    instance: 2
    type: temperature
    name: bedroom_temp

#
# MQTT specific settings
#
mqtt:
  broker:   <ip address: port>
  username: <mqtt username>
  password: <mqtt password>
  
```
