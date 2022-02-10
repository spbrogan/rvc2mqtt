FROM python:3.10-slim-bullseye

WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD rvc2mqtt .
WORKDIR /app
COPY setup.py setup.py
COPY readme.md readme.md
#COPY requirement.txt requirement.txt
run pip install --upgrade setuptools
#RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir -e .

CMD python3 -m rvc2mqtt.app