#!/bin/sh
set -e

git pull
docker-compose -f ../docker-compose.production.yml build --force-rm
COMPOSE_HTTP_TIMEOUT=600 docker-compose -f ../docker-compose.production.yml up -d --scale spider=8
