#FROM python:3.9-slim-buster
ARG BUILD_FROM
FROM $BUILD_FROM

RUN \
  apk add --no-cache \
    python3 pip3


WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD ../rvc2mqtt .
WORKDIR /app
COPY ../setup.py /
COPY ../readme.md /
COPY ../requirement.txt /
COPY ./default_config.yaml /
COPY ./run.sh /

RUN pip3 install -r requirement.txt
RUN pip3 install --no-cache-dir --no-use-pep517 -e .
RUN chmod a+x /run.sh

CMD ["/run.sh"]