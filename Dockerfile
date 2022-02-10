FROM python:3.10-slim-buster

WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD rvc2mqtt .
WORKDIR /app
COPY setup.py setup.py
COPY readme.md readme.md
COPY requirement.txt requirement.txt
RUN pip3 install -r requirement.txt
#RUN pip3 install --no-cache-dir -e .

#CMD python3 -m rvc2mqtt.app
CMD python3 rvc2mqtt/app.py