FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TERM=xterm-256color

RUN groupadd --gid 10001 challenge \
    && useradd --uid 10001 --gid challenge --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin challenge \
    && useradd --uid 10002 --gid challenge --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin reward
WORKDIR /app

COPY --chown=challenge:challenge engine ./engine
COPY --chown=challenge:challenge levels ./levels
COPY --chown=challenge:challenge reward ./reward
COPY --chown=challenge:challenge security ./security
COPY --chown=challenge:challenge main.py server.py runtime.py launch.py ./

CMD ["python3", "launch.py"]
