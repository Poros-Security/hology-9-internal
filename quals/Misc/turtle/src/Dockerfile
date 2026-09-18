FROM python:3.9-alpine

RUN apk add --no-cache socat

WORKDIR /home/ctf/chall

COPY chall.py .
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN chmod 555 chall.py

CMD ["socat", "TCP-LISTEN:8013,reuseaddr,fork", "EXEC:python3 -u /home/ctf/chall/chall.py"]
