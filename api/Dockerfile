FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inscricoes ./inscricoes

ENV DB_PATH=/data/inscricoes.db

EXPOSE 8000

# 1 processo (o limite de envios por IP fica em memória) com algumas threads
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "inscricoes:create_app()"]
