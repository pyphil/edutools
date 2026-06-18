FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Systemnutzer für die App anlegen
RUN addgroup --system app && adduser --system --group app

# Python-Abhängigkeiten installieren
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Projekt kopieren
COPY . /app/

# Verzeichnisse für SQLite, Media und Static vorbereiten
RUN mkdir -p /data/media /app/public/static \
    && chown -R app:app /app /data

USER app

EXPOSE 8000

CMD ["gunicorn", "edutools_site.wsgi:application", "--bind", "0.0.0.0:8000"]