# syntax=docker/dockerfile:1

FROM docker.io/library/python:3.10.12-slim

WORKDIR /tmp/env

COPY build build

RUN pip install -r build/requirements.txt \
    && groupadd -g 1003 myuser \
    && useradd -m -l -u 1003 -g myuser myuser 

COPY src /home/myuser/src

WORKDIR /home/myuser/src

RUN rm -rf /tmp/env && chmod +x run.sh

USER myuser

ENTRYPOINT ["./run.sh"]