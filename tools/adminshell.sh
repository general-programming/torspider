#!/bin/sh

# Should be safe to run on both the host and the container.
unset SOCKS_PROXY
unset HTTP_PROXY
unset HTTPS_PROXY

# Assuming code for the dev setup is not kept in /app/torspider, we should be fine.
if [ -d "/app/torspider" ]; then
    # Container
    # It helps to have the HTTP url for pulling and SSH url for pushing since keys are not copied.

    # Install admin tools.
    apk update
    apk add postgresql-client redis zsh nano less git
    pip install pyreadline ipython

    # Uninstall and reinstall as a development environment.
    pip uninstall -y torspider
    python setup.py develop

    # Setup aliases and drop to a shell.
    echo "alias redis-cli='redis-cli -h $REDIS_HOST -p $REDIS_PORT'" >> ~/.zshrc
    zsh -i
else
    # Boot up an admin container!
    docker-compose -f ../docker-compose.production.yml run --rm -u 0 spider tools/adminshell.sh
fi
