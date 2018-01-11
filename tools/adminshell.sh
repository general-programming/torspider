#!/bin/sh

# Should be safe to run on both the host and the container.
unset SOCKS_PROXY
unset HTTP_PROXY
unset HTTPS_PROXY

# Assuming code for the dev setup is not kept in /app/torspider, we should be fine.
if [ -d "/app/torspider" ]; then
    # Container
    apk update
    apk add postgresql-client redis zsh busybox-extras nano less
    pip install pyreadline ipython
    echo "alias redis-cli='redis-cli -h $REDIS_HOST -p $REDIS_PORT'" >> ~/.zshrc
    zsh -i
else
    # Boot up an admin container!
    docker-compose run --rm -u 0 spider tools/adminshell.sh
fi
