# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /app

COPY ../ .
RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir --no-use-pep517 -e .

CMD python3 rvc2mqtt/app.py -i can0 -v -v