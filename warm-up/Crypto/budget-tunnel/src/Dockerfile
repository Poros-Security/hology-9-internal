FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r ctf && useradd -r -g ctf -d /app -s /usr/sbin/nologin ctf
RUN python3 -m pip install --no-cache-dir pycryptodome
COPY --chown=ctf:ctf Chall.py /app/Chall.py
USER ctf
EXPOSE 31341
CMD ["python3", "/app/Chall.py"]
