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

go read the latest on <https://raspberrypi.com>
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

See configuration.md

### Build and deploy with docker

see docker_deploy.md



