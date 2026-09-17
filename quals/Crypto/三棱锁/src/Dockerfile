FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY challenge.py description.txt server.py ./

ENV PORT=8001
ENV CHALLENGE_NAME="三棱锁"

EXPOSE 8001

CMD ["python3", "server.py"]
