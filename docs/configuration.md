# Configuration

There are three different files used for configuration.  These are in yaml format (json is valid yaml).  

## Floor plan 1 or 2

These two files are both optional but without some floor plan nodes this software doesn't do anything.  These files contain a `floorplan` node and then have subnodes with the different devices in your RV.  A device should only be defined in one floor plan file. The main reason to allow for 
two input files is to easily support a "HA addon" where a main file might exist and then user entered 
text from the WebUI might be written to floor plan 2.   

### Example

``` yaml

floorplan:
  - name: DC_LOAD_STATUS
    instance: 1
    type: light_switch
    instance_name: bedroom light

  - name: DC_LOAD_STATUS
    instance: 2
    type: light_switch
    instance_name: living room light

  - name: DC_LOAD_STATUS
    instance: 8
    type: light_switch
    instance_name: awning light

  - name: THERMOSTAT_AMBIENT_STATUS
    instance: 2
    type: temperature
    instance_name: bedroom temperature

  - name: TANK_STATUS
    instance: 0
    type: tank_level
    instance_name: fresh water tank

  - name: TANK_STATUS
    instance: 1
    type: tank_level
    instance_name: black waste tank

  - name: TANK_STATUS
    instance: 2
    type: tank_level
    instance_name: rear gray waste tank

  - name: TANK_STATUS
    instance: 18
    type: tank_level
    instance_name: galley gray waste tank

  - name: TANK_STATUS
    instance: 20
    type: tank_level
    instance_name: what tank is this 20

  - name: TANK_STATUS
    instance: 21
    type: tank_level
    instance_name: what tank is this 21

  - name: WATER_PUMP_STATUS
    type: water_pump
    instance_name: fresh water pump

  - name: WATERHEATER_STATUS
    type: waterheater
    instance: 1
    instance_name: main waterheater

  - name: DC_LOAD_STATUS
    type: tank_warmer
    instance: 34
    instance_name: waste tank heater

  - name: DC_LOAD_STATUS
    type: tank_warmer
    instance: 35
    instance_name: fresh water tank heater

```


## Log Config File

This is optional and allows for complex logging to be setup.  If provided the yaml file needs to follow 
<https://docs.python.org/3/library/logging.config.html#logging-config-dictschema>

If not provided the app will do basic docker logging.


## Example

This example setups up 3 log files and a basic logger to console.  It assumes you have a volume mapped at 
`/config` of the container.  

`RVC2MQTT.log` is a basic INFO level logger for the app
`RVC_FULL_BUS_TRACE.log` will capture all rvc messages (in/out)  
`UNHANDLED_RVC.log` will capture all the rvc messages that are not handled by an object.

``` yaml
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
      level: INFO
      class: logging.FileHandler
      formatter: default
      filename: /config/RVC2MQTT.log
      mode: w
    unhandled_file_handler:
      level: DEBUG
      class: logging.FileHandler
      formatter: time-only
      filename: /config/UNHANDLED_RVC.log
      mode: w
    rvc_bus_trace_handler:
      level: DEBUG
      class: logging.FileHandler
      formatter: time-only
      filename: /config/RVC_FULL_BUS_TRACE.log
      mode: w

  loggers:
    "": # root logger
      handlers:
        - debug_console_handler
        - debug_file_handler
      level: DEBUG
      propagate: False

    "unhandled_rvc": # unhandled messages
      handlers:
        - unhandled_file_handler
      level: DEBUG
      propagate: False

    "rvc_bus_trace": # all bus messages
      handlers:
        - rvc_bus_trace_handler
      level: DEBUG
      propagate: False

  formatters:
    brief:
      format: "%(message)s"
    time-only:
      format: "%(asctime)s   %(message)s"
      datefmt: "%d %H:%M:%S"
    default:
      format: "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
      datefmt: "%Y-%m-%d %H:%M:%S"

```
