FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Online-Demo: leere Datenbank beim Start mit Beispieldaten füllen (DEMO_SEED=0 deaktiviert)
ENV DEMO_SEED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# PORT wird von Hosting-Plattformen (z. B. Render) gesetzt, lokal Fallback 8000
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
