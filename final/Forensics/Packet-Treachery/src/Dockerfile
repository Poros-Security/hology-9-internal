cat > src/Dockerfile <<'EOF'
FROM python:3.11-alpine

RUN apk update && apk add --no-cache socat

RUN adduser -D -u 1001 -s /bin/sh ctf

RUN mkdir -p /home/ctf/chall/src

COPY ./requirements.txt /home/ctf/chall
RUN pip3 install --no-cache-dir -r /home/ctf/chall/requirements.txt

COPY ./chall.py   /home/ctf/chall/src/
COPY ./run.sh     /home/ctf/chall/src/
COPY ./flag.txt   /home/ctf/chall/src/

RUN chown -R root:root /home/ctf/chall \
 && chmod -R 555 /home/ctf/chall \
 && chmod 444 /home/ctf/chall/src/flag.txt

USER ctf
WORKDIR /home/ctf/chall/src

EXPOSE 11133
CMD ["./run.sh"]
EOF
