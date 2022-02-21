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
This has been developed/used on Raspberry Pi OS Lite (debian bullseye & buster) but since docker is used
for the application environment dependencies are minimal.

### Enable CanBus support in Kernel

See the waveshare doc here: <https://www.waveshare.com/w/upload/2/29/RS485-CAN-HAT-user-manuakl-en.pdf>
For debian bullseye and buster nothing additional was needed but if using older/other kernel versions you
may need to add/enable the kernel modules. 


### Update /boot/config.txt to enable rs485 can hat

If you are using HomeAssistantOS you will need to remove the SD card, insert into anothe PC, and find the file on the boot partition.
This can be done by inserting into a Windows machine as the boot drive is visible.

``` ini
[all]
#dtoverlay=vc4-fkms-v3d

dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000
```

### Bring up the can network

There are a lot of different services that manage the network hardware on linux.  You will need to find what
is right for your distribution.  

For debian bullseye the following process worked.  

Make new can0.conf file in /etc/network/interfaces.d 

``` ini
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 250000 restart-ms 100
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down
```

![image](https://user-images.githubusercontent.com/2954441/154997242-382360da-9898-47f6-8517-8f01b10d32de.png)

Manually from the cli this can be done by issuing the following commands

``` bash
sudo ip link set can0 type can

sudo ip link set can0 up
```

### Make a floorplan.yaml file and/or logging.yaml in a folder you can mount as /config for the container

See [configuration.md](configuration.md)

### deploy with docker

see docker_deploy.md



