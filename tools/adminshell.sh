#!/bin/sh

# Assuming code for the dev setup is not kept in /app/torspider, we should be fine.
if [ -d "/app/torspider" ]; then
    # Container
    apk add --no-cache postgresql-client redis zsh busybox-extrask
    echo 'alias redis-cli=redis-cli -h $REDIS_HOST -p $REDIS_PORT' >> ~/.zshrc
    zsh -i
else
    # Boot up an admin container!
    docker-compose run --rm spider tools/adminshell.sh
fi
