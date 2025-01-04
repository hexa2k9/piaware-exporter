FROM python:3.13-alpine3.20 AS builder

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /work
ADD requirements.txt /work

RUN set -eux \
  && pip install virtualenv \
  && virtualenv /opt/virtualenv \
  && /opt/virtualenv/bin/pip install -r requirements.txt

FROM python:3.13-alpine3.20

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN set -eux \
    && apk --no-cache upgrade

ADD piaware_exporter /opt/piaware-exporter
COPY --from=builder /opt/virtualenv /opt/virtualenv

EXPOSE 9101

ENTRYPOINT ["/opt/virtualenv/bin/python", "/opt/piaware-exporter/main.py"]
CMD ["--help"]
