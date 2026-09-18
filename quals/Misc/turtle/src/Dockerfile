FROM python:3.9-alpine

RUN apk add --no-cache \
    git \
    build-base

# Build ynetd
WORKDIR /tmp

RUN git clone --depth 1 https://github.com/johnsonjh/ynetd.git \
    && cd ynetd \
    && make \
    && cp ynetd /usr/local/bin/ynetd

# User challenge
RUN adduser -D -u 1001 -s /bin/sh ctf

RUN mkdir -p /home/ctf/chall

COPY requirements.txt /home/ctf/chall/requirements.txt

RUN pip3 install \
    --no-cache-dir \
    -r /home/ctf/chall/requirements.txt

COPY chall.py /home/ctf/chall/chall.py
COPY run.sh /home/ctf/chall/run.sh

RUN chmod 555 /home/ctf/chall/chall.py \
    && chmod 555 /home/ctf/chall/run.sh \
    && chown -R root:root /home/ctf/chall

USER ctf
WORKDIR /home/ctf/chall

CMD ["./run.sh"]
