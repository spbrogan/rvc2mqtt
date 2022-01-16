# docker

Plan is to deploy using docker. 
For now you must build your own.

## build it

```bash
docker build -t rvc2mqtt .
```

## run it

Map in the host network so that the can0 bus is present.  
TODO: figure out better way maybe using --cap-add=NET_ADMIN
Might need to bring up the can0 interface like

```bash
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 250000
```
Then to run the docker image

```bash
docker run --network=host --restart=always -v ~/config:/config -v ~/config:/log rvc2mqtt 
```

## run in the container yourself

```bash
docker run --network=host --restart=always -v ~/config:/config -v ~/config:/log -it rvc2mqtt bash
```
