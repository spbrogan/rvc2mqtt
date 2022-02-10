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

See the waveshare doc here: <https://www.waveshare.com/w/upload/2/29/RS485-CAN-HAT-user-manuakl-en.pdf>

### Update /boot/config.txt to enable rs485 can hat

If you are using HomeAssistantOS you will need to remove the SD card and find the file on the boot partition.  

_still need to see if this survives an update_

``` ini
[all]
#dtoverlay=vc4-fkms-v3d

dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000
```

### Bring up the can network

TBD - figure out how to do automatically.  Too many different linux network services

Manually this can be done doing

``` bash
sudo ip link set can0 type can

sudo ip link set can0 up
```

### Make a floorplan.yaml file and/or logging.yaml in a folder you can mount as /config for the container

See [configuration.md](configuration.md)

### deploy with docker

see docker_deploy.md



