# MQTT 

This details the usage of the MQTT protocol for information, status and command sharing.

MQTT is infinitely flexible so this is intended to provide insight into usage by the rvc2mqtt project. 

## Config and requirements

This project does not provide an MQTT broker.

This project requires a network connection to an existing broker
and credentials that allow publish/subscribe privileges to at least the rvc
base topic. 

This schema can support multiple rvc2mqtt bridges
using the client-id to provide an isolated namespace.  Please make sure this is unique if you
have more than one bridge 

```yml
mqtt:
  broker:    <ip address>:<optional port>
  username:  <user name>
  password:  <password>
  client-id: <client-id> #optional default=bridge

```

## Topic hierarchy

rvc2mqtt uses the following topic hierarchy.
Information about the bridge device (this device)
is located at here:
`rvc2mqtt/<client-id>`  

More specifically:
`rvc2mqtt/<client-id>`       - this reports the connected state of our bridge to the mqtt broker (`online` or `offline`)
`rvc2mqtt/<client-id>/info`  - contains json defined metadata about this bridge and the rvc2mqtt software

Devices managed by rvc2mqtt are listed by their unique device id
`rvc2mqtt/<device-id>`

### Light

The Light object is used to describe a light.
A light can have on / off

| Topic             | rvc2mqtt operation | Description                     |
|---                | :---:              | ---                             |
|`<device-id>`      | publish            | status of light (`on` or `off`) |
|`<device-id>cmd`   | subscribe          | command the light with payload `on` or `off` |
|`<device-id>/info` | publish            | json data with more attributes and info about light |


### Temperature Sensor

A very simple RVC device that reports temperature in C
This sensor has no configuration and will just have a state value in C
It does not subscribe to any topics
It only updates the mqtt topic when the temperature changes.

| Topic                         | rvc2mqtt operation | Description                     |
|---                            | :---:              | ---                             |
|`<device-id>`      | publish            | temperature in C |


### HVAC

The HVAC objet is used to control heat, cool, fan, and temperature

TBD

## Home Assistant Integration

Home assistant has created mqtt auto-discovery.  This describes how rvc2mqtt integrates
with mqtt auto-discovery.

TBD
