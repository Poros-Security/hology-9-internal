FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ml_model.py train_model.py ./
COPY model/ ./model/
COPY static/ ./static/
COPY templates/ ./templates/

EXPOSE 5000

CMD ["python", "app.py"]
