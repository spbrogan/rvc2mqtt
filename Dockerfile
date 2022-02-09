FROM python:3.9-slim-buster

WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD rvc2mqtt .
WORKDIR /app
COPY setup.py setup.py
COPY readme.md readme.md
#COPY requirement.txt requirement.txt

#RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir --no-use-pep517 -e .

CMD python3 -m rvc2mqtt.app -f ${FLOORPLAN} -l ${LOG_CONFIG_FILE}