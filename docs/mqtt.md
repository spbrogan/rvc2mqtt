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
mqtt:d
  brokerd: <ip address>:<optional port>
  username: <user name>
  password: <password>
  client-id: <client-id> #optional default=bridge

```

## Topic hierarchy

rvc2mqtt uses the following topic hierarchy.
Information about the bridge device (this device)
is located at here:
`rvc/<client-id>`  

More specifically:
`rvc/<client-id>/state`   - this reports the connected state of our bridge to the mqtt broker (`on` or `off`)
`rvc/<client-id>/info`    - contains json defined metadata about this bridge and the rvc2mqtt software
`rvc/<client-id>/devices` - contains the devices.  The hierarchy for specific device types are below

### Light

The Light object is used to describe a light.
A light can have brightness control from 0 - 100%
A light can have on / off

| Topic                         | rvc2mqtt operation | Description                     |
|---                            | :---:              | ---                             |
|`<device-id>/light/state`      | publish            | status of light (`on` or `off`) |
|`<device-id>/light/cmd`        | subscribe          | command the light with payload `on` or `off` |
|`<device-id>/brightness/state` | publish            | brightness percentage between (0 - 100) | rvc2mqtt will publish |
|`<device-id>/brightness/cmd`   | subscribe          | set the brightness | rvc2mqtt will publish |
|`<device-id>/info`             | publish            | json data with more attributes and info about light |

### HVAC

The HVAC objet is used to control heat, cool, fan, and temperature

TBD

## Home Assistant Integration

Home assistant has created mqtt auto-discovery.  This describes how rvc2mqtt integrates
with mqtt auto-discovery.

TBD
