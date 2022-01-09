FROM python:3.9-slim-buster

WORKDIR /app

ADD rvc2mqtt .
COPY setup.py setup.py
COPY readme.md readme.md
COPY requirement.txt requirement.txt


RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir --no-use-pep517 -e .

CMD python3 rvc2mqtt/app.py -i can0 -v -v