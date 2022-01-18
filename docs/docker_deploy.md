# docker

Plan is to deploy using docker. 
For now you must build your own.

## build it

```bash
docker build -t rvc2mqtt .
```

## config file

The image expects a config file located at /config/config.yaml
You should bind a host directory to this with your config.yaml.
It also works well for your log files

See configuration.md for a sample config.yaml

## run it

Map in the host network so that the can0 bus is present.  
TODO: figure out better way maybe using --cap-add=NET_ADMIN
Might need to bring up the can0 interface on host like

```bash
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 250000
```
Then to run the docker image

```bash
docker run --network=host --restart=always -v ~/config:/config rvc2mqtt 
```

## run in the container yourself

```bash
docker run --network=host --restart=always -v ~/config:/config -it rvc2mqtt bash
```
