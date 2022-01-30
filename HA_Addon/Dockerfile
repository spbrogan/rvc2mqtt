#FROM python:3.9-slim-buster
ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /app
WORKDIR /app/rvc2mqtt
ADD ./rvc2mqtt .
WORKDIR /app
COPY ./setup/setup.py /
COPY ./setup//readme.md /
COPY ./setup/requirement.txt /
COPY ./default_config.yaml /
COPY ./run.sh /

RUN \
  apk add --no-cache \
    python3 \
    pip3 \
    && pip3 install -r requirement.txt \
    && pip3 install --no-cache-dir --no-use-pep517 -e . \
    && chmod a+x /run.sh

COPY rootfs /

CMD ["/run.sh"]