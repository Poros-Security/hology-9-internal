FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r ctf && useradd -r -g ctf -d /app -s /usr/sbin/nologin ctf
COPY --chown=ctf:ctf server.py qna.json ./
USER ctf
EXPOSE 1133
CMD ["python3", "server.py"]
