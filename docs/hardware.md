# Hardware Setup

rvc2mqtt uses python-can and thus *should* work with anything supported by python-can. 

## Tested Hardware (Pi Zero 2W)

RaspberryPi Zero 2 W

Waveshare RS485 CAN HAT
<https://www.amazon.com/gp/product/B07VMB1ZKH/ref=ox_sc_act_title_1?smid=A3B0XDFTVR980O&psc=1>


## Tested Hardware (Pi 3 B+)

details to come

## Software

### Install latest version of Raspbian

go read the latest on raspberrypi.com
This has been used on Raspberry Pi OS Lite 

### Enable CanBus support in Kernel

* Add waveshare doc and steps here

### Bring up the can network

TBD - figure out how to do automatically.  Too many different linux network services

Manually this can be done doing

``` bash
sudo ip link set can0 type can bitrate 250000

sudo ip link set can0 up
```

### Make a config.yaml file in a folder you can mount as /config for the container

```yaml
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
      stream: ext://sys.stdout
    debug_file_handler:
      level: DEBUG
      class: logging.FileHandler
      filename: /log/rvc_debug.log
      mode: a
  loggers: 
    '': # root logger
      handlers: 
        - debug_console_handler
        - debug_file_handler
      level: DEBUG
      propagate: False

#
# RV - floorplan
#
map: 
  - dgn: 1FFBC
    instance: 1
    group: 0
    type: "Light"
    add:
      friendly_name: "bedroom light"
  - dgn: 1FFBC
    instance: 2
    group: 0
    type: "Light"
    add:
      friendly_name: "main light"

#
# MQTT specific settings
#
mqtt:
  broker:   <ip addr>:<port>
  username: <your username>
  password: <your password>
  
```


## Docker


