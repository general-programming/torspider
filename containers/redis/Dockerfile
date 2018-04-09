FROM redis:4.0.9-alpine

RUN set -ex; \
    apk add --no-cache --virtual .build-deps coreutils gcc make musl-dev git; \
    git clone https://github.com/RedisLabsModules/rebloom.git; \
    cd rebloom; \
    make; \
    mv rebloom.so /usr/local/lib/rebloom.so; \
    cd ..; \
    rm -rf rebloom; \
    apk del .build-deps
