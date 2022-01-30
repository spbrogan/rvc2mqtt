#FROM python:3.9-slim-buster
ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /app
ADD ./rvc2mqtt .
COPY ./setup/setup.py .
COPY ./setup/readme.md .
COPY ./setup/requirement.txt .
COPY ./default_config.yaml .
COPY ./run.sh .

RUN \
    pip3 install -r ./requirement.txt \
    && pip3 install --no-cache-dir --no-use-pep517 -e . \
    && chmod a+x ./run.sh

CMD ["./run.sh"]