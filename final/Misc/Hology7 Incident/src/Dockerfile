FROM python:3.12-slim

WORKDIR /app

COPY server.py ./server.py
COPY puzzles.json ./puzzles.json
COPY static ./static

ENV PORT=8085

EXPOSE 8085

CMD ["python3", "server.py"]
