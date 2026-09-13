# Faz 1 T038 — matrix servisi imajı.
FROM python:3.13-slim

WORKDIR /app
COPY services/matrix/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/matrix/app ./services/matrix/app
COPY services/__init__.py ./services/__init__.py
COPY services/matrix/__init__.py ./services/matrix/__init__.py

EXPOSE 8080
CMD ["uvicorn", "services.matrix.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
