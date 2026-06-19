# Docker Deployment Guide for edutools

This guide explains how to run the Django app with Nginx using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- The `.env` file configured (see below)

## Quick Start

### 1. Configure Environment Variables

**For local development:**
```bash
cp .env.example .env
# Edit .env as needed
```

**For Docker deployment:**
```bash
cp .env.docker .env
# Edit .env and update:
# - SECRET_KEY (must be unique in production)
# - ALLOWED_HOSTS (your domain)
# - Email credentials
# - CSRF_TRUSTED_ORIGINS
```

### 2. Build and Start Containers

```bash
docker-compose up -d
```

This will:
- Build the Django image
- Create Django and Nginx containers
- Run database migrations automatically
- Collect static files automatically
- Start both services

### 3. Access the Application

- **Application:** http://localhost
- **Admin:** http://localhost/admin

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f nginx
```

## Environment Configuration

### Local Development (existing setup)
The `.env` file is used as-is for local development. The Django settings load it automatically with sensible defaults.

### Docker Deployment
When using Docker Compose, the `.env` file is passed to the Django container, but environment variables are **overridden** in `docker-compose.yml` to use Docker volume mount paths:

```yaml
environment:
  SQLITE_PATH: /app/data/db.sqlite3      # Points to volume
  STATIC_ROOT: /app/public/static         # Points to volume
  MEDIA_ROOT: /app/media                  # Points to volume
```

This ensures:
- Database persists in the `data/` volume
- Static files are collected to `public/static/` volume
- Media uploads go to `media/` volume

## Directory Structure

```
edutools/
├── data/                    # Docker volume - SQLite database
├── media/                   # Docker volume - User uploaded files
├── public/static/           # Docker volume - Collected static files
├── Dockerfile               # Django image definition
├── docker-compose.yml       # Service orchestration
├── nginx.conf              # Nginx configuration
├── .env                    # Environment variables
├── .env.docker             # Docker example configuration
└── manage.py
```

## Common Commands

### Development
```bash
# Local development (without Docker)
python manage.py runserver

# Migrate database locally
python manage.py migrate

# Collect static files locally
python manage.py collectstatic
```

### Docker Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild image after code changes
docker-compose build

# Rebuild and restart (pull fresh code)
docker-compose up -d --build

# Access Django shell
docker-compose exec django python manage.py shell

# Run migrations manually
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser

# Collect static files manually
docker-compose exec django python manage.py collectstatic --noinput

# View database
docker-compose exec django python manage.py shell
```

## Volumes

Three volumes persist data across container restarts:

1. **data/** - SQLite database (`db.sqlite3`)
2. **media/** - User-uploaded files (photos, files, etc.)
3. **public/static/** - Collected static files (CSS, JS, images)

All volumes are excluded from git via `.gitignore`.

## Nginx Configuration

The `nginx.conf` includes:
- Static file serving with 30-day caching
- Media file serving with 7-day caching
- Reverse proxy to Django (port 8000)
- Gzip compression
- HTTPS support (commented, ready to uncomment)

### For HTTPS/SSL

1. Mount your certificates to the nginx container
2. Uncomment the HTTPS server block in `nginx.conf`
3. Update `docker-compose.yml` to mount certificates:
   ```yaml
   volumes:
     - ./certs:/etc/nginx/certs:ro
   ```

## Troubleshooting

### "Cannot connect to Docker daemon"
```bash
# Make sure Docker is running
docker --version
```

### "Port 80 already in use"
```bash
# Use different port in docker-compose.yml
ports:
  - "8080:80"    # Access at http://localhost:8080
```

### "Database locked"
SQLite can have locking issues with multiple processes. If you see this:
1. Stop containers: `docker-compose down`
2. Delete the database: `rm data/db.sqlite3`
3. Restart: `docker-compose up -d`

### "Static files not loading"
```bash
# Collect static files manually
docker-compose exec django python manage.py collectstatic --noinput

# Restart nginx
docker-compose restart nginx
```

### "Permission denied on volumes"
```bash
# Fix volume permissions
sudo chown -R 1000:1000 data media public/static
```

## Production Considerations

For production deployment:

1. **SECRET_KEY**: Generate a strong, unique key
2. **DEBUG**: Set to `False`
3. **ALLOWED_HOSTS**: List your actual domains
4. **CSRF_TRUSTED_ORIGINS**: Include your domain with https://
5. **HTTPS**: Uncomment and configure SSL certificates
6. **Backups**: Backup the `data/` and `media/` volumes regularly
7. **Logs**: Configure centralized logging (mount volumes for persistent logs)
8. **Health checks**: Monitor container health via `docker ps`

## Switching Between Local and Docker

To switch between local development and Docker:

### Use Docker
```bash
# Copy docker config
cp .env.docker .env
docker-compose up -d
```

### Use Local Development
```bash
# Reset .env to local settings
cp .env.example .env
# Edit .env as needed (remove SQLITE_PATH, STATIC_ROOT, MEDIA_ROOT or set to local paths)
python manage.py runserver
```

The `.env` file supports both environments - locally-set paths work for local dev, and Docker override them with volume mount paths.
