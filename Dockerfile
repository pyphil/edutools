FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create directories for volumes
RUN mkdir -p /app/data /app/media /app/public/static

# Collect static files (will fail if DEBUG=False without a static root, but that's ok for this stage)
RUN python manage.py collectstatic --noinput --ignore=*.scss || true

# Create a non-root user
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "edutools_site.wsgi:application"]
