#!/bin/sh

# Assuming code for the dev setup is not kept in /app/torspider, we should be fine.
if [ -d "/app/torspider" ]; then
    # Container
    apk update
    socks_proxy="" apk add postgresql-client redis zsh busybox-extras nano less
    echo "alias redis-cli='redis-cli -h $REDIS_HOST -p $REDIS_PORT'" >> ~/.zshrc
    zsh -i
else
    # Boot up an admin container!
    docker-compose run --rm -u 0 spider tools/adminshell.sh
fi
