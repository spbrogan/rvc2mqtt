# docker

Plan is to deploy using docker. 
For now you must build your own.

## build it

```bash
docker build -t rvc2mqtt .
```

## run it

```bash
docker run rvc2mqtt 
```

## run it interactively 

```bash
docker run rvc2mqtt bash
```

## run it with verbose debug

```bash
docker run rvc2mqtt python3 rvc2mqtt/app.py -i can0 -v -v
```

## change an input parameter like interface

```bash
docker run rvc2mqtt python3 rvc2mqtt/app.py -i <your interface here>
```