FROM python:3.9-slim-buster

WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD rvc2mqtt .
WORKDIR /app
COPY setup.py setup.py
COPY readme.md readme.md
COPY requirement.txt requirement.txt


RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir --no-use-pep517 -e .

CMD python3 rvc2mqtt/app.py -i can0