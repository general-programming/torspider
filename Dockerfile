FROM python:3.6.5-alpine

# Create limited user for Celery
RUN adduser -D -u 1000 -h /app appuser

# Set WORKDIR to /app
WORKDIR /app

# Requirements
COPY requirements.txt /app/requirements.txt
RUN apk add --no-cache build-base libffi libffi-dev ca-certificates pkgconf postgresql-dev ca-certificates libxml2-dev libxslt-dev tini libmagic openssl-dev && \
	CPPFLAGS=-I/usr/include/libxml2 pip3 install -r /app/requirements.txt

# Add code
COPY . /app
RUN python3 setup.py install

# Set user
USER appuser

# Tini entrypoint
ENTRYPOINT ["/sbin/tini", "--"]
