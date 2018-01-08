#!/bin/sh
set -e

git pull
docker-compose build --force-rm
COMPOSE_HTTP_TIMEOUT=600 docker-compose up -d --scale spider=8
