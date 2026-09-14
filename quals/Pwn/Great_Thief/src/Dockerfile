FROM alpine:3.19

RUN apk update && apk add --no-cache socat gcc musl-dev coreutils

RUN adduser -D -u 1001 -s /bin/sh ctf
RUN mkdir /home/ctf/chall
RUN mkdir /home/ctf/chall/src

COPY ./chall.c /home/ctf/chall/src
COPY ./run.sh /home/ctf/chall/src

WORKDIR /home/ctf/chall/src

RUN gcc chall.c -o chall     -fno-stack-protector     -no-pie     -z norelro     -z noexecstack     -w

RUN rm chall.c
RUN chown -R root:root /home/ctf/chall
RUN chmod -R 555 /home/ctf/chall
RUN chmod 555 /home/ctf/chall/src/chall

USER ctf
WORKDIR /home/ctf/chall/src
CMD ["./run.sh"]
