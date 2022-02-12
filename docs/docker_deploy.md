# docker

Plan is to deploy using docker. 

Builds are available for released version and `main` branch.
<https://github.com/spbrogan/rvc2mqtt/pkgs/container/rvc2mqtt>

Image: `ghcr.io/spbrogan/rvc2mqtt:main`

## Settings and configuration

The image uses environment variables for all configuration and file paths.

`CAN_INTERFACE_NAME` : the network can interface name.  default value: `can0`

`FLOORPLAN_FILE_1` : path to the floor plan file.  Recommendation is mount a volume from the host with your floor plan

`FLOORPLAN_FILE_2` : path to the 2nd floor plan file.  This is optional but for HA addons this allows UI generated content to be added.

`LOG_CONFIG_FILE` : path to a logging configuration file.  Optional yaml file for more complex logging options.

`MQTT_HOST` : host url for mqtt server

`MQTT_PORT` : host port for mqtt server

`MQTT_USERNAME` : username to connect with

`MQTT_PASSWORD` : password to connect with

`MQTT_CLIENT_ID` : mqtt client id and the bridge node name in mqtt path.  default is `bridge`

Optional values if using TLS (not implemented yet!)

`MQTT_CA` : CA cert for Mqtt server  
`MQTT_CERT` : Cert for client  
`MQTT_KEY` : key for mqtt

See configuration.md for a sample files are more details.

## run it

Map in the host network so that the can0 bus is present.  
TODO: figure out better way maybe using --cap-add=NET_ADMIN
Might need to bring up the can0 interface on host like

```bash
sudo ip link set can0 down
sudo ip link set can0 up type can
```
Then to run the docker image

you will need to setup a bunch of env variables so the command is pretty length.  Sorry.  A docker compose file would probably be helpful.

## build it locally

```bash
docker build -t rvc2mqtt .
```
