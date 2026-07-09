

<div align="center">
  <img src="./edutools_home/static/images/edutools_gear.png" alt="eduTools">
</div>
<div align="center">
<b>eduTools</b>
</div>

# eduTools

*eduTools* is a collection of Django web applications that have been developed to meet the needs of the teaching staff at our secondary school. The applications are currently only available in German. 

*eduTools* contains: 
- **Booking tool:** for rooms and equipment. Students can enter their names on a digital borrowing list for iPads and their pens.
- The booking tool includes a **Support Ticket System** for all devices to make work easier for school administrators.
- **WLAN Codes:** Issue/display of Wi-Fi codes for students, which also includes management of permanent Wi-Fi codes for the admins.
- **MKR:** An application that enables the NRW media competence framework to be developed collaboratively and presented in a padlet-like structure. There is also a subject-specific export option for the internal curricula.
- **Library Manager:** A simple school library management system including a function to borrow books from the library.
- **QR Code Generator** with management of the generated codes
- **Appointment:** Enables parents to book an appointment, e.g. for the school's registration procedure, while school staff can manage the appointments and print lists in the backend.
- **Activity:** Enables parents to book different kind of activities, e.g. to organize the Open Day.
- **Digital notice board** also displaying the school's substitute teacher schedule

*eduTools* includes self-registration for teachers based on their school email addresses.

---
### DE

*eduTools* ist eine Sammlung an Django-Web-Applikationen, die entlang der Bedürfnisse des Kollegiums an unserer weiterführenden Schule entwickelt wurden. Die Anwendungen sind bisher nur auf Deutsch verfügbar. 

*eduTools* enthält: 
- **Buchungstool:** für Räume und Geräte. Schüler können sich in eine digitale Ausleihliste für iPads und deren Stifte eintragen.
- im Buchungstool enthalten ist ein **Support Ticket System** für alle Geräte um den Schuladministatoren die Arbeit zu erleichtern.
- **WLAN-Codes:** Ausgabe/Anzeige von WLAN-Codes für Schüler:innen, das auch eine Verwaltung von Dauer-WLAN-Codes für die Admins enthält.
- **MKR:** Eine Anwendung, die es ermöglich den NRW Medienkompetenzrahmen kollaborativ zu erarbeiten und in einer Padlet-artigen Struktur darzustellen. Zudem gibt es eine fachspezifische Exportmöglichkeit für die internen Lehrpläne.
- **Library Manager:** Eine einfache Schulbibliotheksverwaltung inklusive Ausleihfunktion.
- **QR-Code Generator** mit Verwaltung der generierten Codes
- **Termin:** Ermöglicht es den Eltern, einen Termin zu buchen, z. B. für das Anmeldeverfahren der Schule, während das Schulpersonal die Termine verwalten und Listen im Backend drucken kann.
- **Aktivität:** Ermöglicht es den Eltern, verschiedene Arten von Aktivitäten zu buchen, z.B. für den Tag der offenen Tür.
- **Digitales Schwarzes Brett** mit Vertretungsplanansicht

*eduTools* enthält eine Selbstregistrierung für Lehrkräfte basierend auf deren Dienst-E-Mail-Adressen.


## Setup Development Server

### Create and activate a Virtual Environment (optional)
```
python3 -m venv .venv       (on Windows: python -m venv .venv)

source .venv/bin/activate   (on Linux and MacOS)

.venv/Scripts/activate      (on Windows)

```

### Get the source code
```
git clone https://github.com/pyphil/edutools.git
```

### Install requirements in virtual environment
```
pip install -r requirements.txt
```

### Migrate database
```
python manage.py migrate
```

### Create superuser for eduTools and Django's /admin/
```
python manage.py createsuperuser
```

### Run local development server
```
python manage.py runserver
```

## Using .env for settings
The project its sensitive settings from a local .env file using django-environ. 
Copy [.env.example](.env.example) to .env and adjust the values for your environment, e.g. for the django secret key, allowed hosts and the email configuration.

For local development, set DEBUG=True, for production always DEBUG=False.

## Simple Production Setup

The following section describes a simple production setup for running eduTools on a Linux server.

> This is a basic deployment example. Depending on your hosting environment, you may need to adjust paths, database settings, web server configuration and security settings.

### Recommended production settings

In production, your `.env` file should contain at least:

```env
DEBUG=False
SECRET_KEY=replace-this-with-a-long-random-secret-key
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

Make sure that:

- `DEBUG` is set to `False`
- `SECRET_KEY` is unique and private
- `ALLOWED_HOSTS` contains your real domain names
- `CSRF_TRUSTED_ORIGINS` contains your HTTPS domain names
- your `.env` file is not committed to Git
- HTTPS is enabled for the domain

### Install the application

Clone the repository on the server:

```bash
git clone https://github.com/pyphil/edutools.git
cd edutools
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the requirements:

```bash
pip install -r requirements.txt
```

Create the `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file and adjust the values for production.

### Prepare the database and static files

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Collect static files:

```bash
python manage.py collectstatic
```

The `collectstatic` command requires a valid `STATIC_ROOT` setting in your Django settings, for example:

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

If the project handles uploaded files, configure media files as well:

```python
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### Run deployment checks

Before going live, run:

```bash
python manage.py check --deploy
```

Review the output and adjust the configuration where necessary.

### Updating an existing production installation

To update an existing installation:

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

Afterwards, restart the application using your hosting environment's restart mechanism.

---

## Example: Production Setup on a vServer with Plesk and Phusion Passenger

Plesk can run Django applications using its Python support, which usually uses **Phusion Passenger** in the background.

The exact interface may differ depending on your Plesk version.

### Example directory structure

One possible setup is:

```text
/var/www/vhosts/example.com/
├── edutools/
│   ├── manage.py
│   ├── passenger_wsgi.py
│   ├── requirements.txt
│   ├── .env
│   ├── edutools_site/
│   ├── edutools_home/
│   └── public/ (the only directory open to the web!)
└── httpdocs/
```

In this example, the Django project is located in:

```text
/var/www/vhosts/example.com/edutools
```

### Set up the Python application in Plesk

In Plesk:

- Open your domain
- Go to **Python**
- Enable Python support
- Set the application root, for example:

```text
/var/www/vhosts/example.com/edutools
```

- Set the application startup file to:

```text
passenger_wsgi.py
```

- Set the application entry point to:

```text
application
```

- Select the Python version you want to use
- Create or select a virtual environment

### Create `passenger_wsgi.py`

Create a file named `passenger_wsgi.py` in the project root, next to `manage.py`:

```python
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edutools_site.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

### Add Plesk Apache settings for passenger
The "additional directives for https" field should contain:

```env
PassengerEnabled On
PassengerAppRoot /full-path-to/httpdocs
PassengerStartupFile passenger_wsgi.py
PassengerAppType wsgi
PassengerPython /full-path-to/.venv/bin/python
```

### Create virtual environment and install requirements

Connect to the server using SSH and go to the project directory:

```bash
cd /var/www/vhosts/example.com/edutools
```

Create virtual python environment:

Activate the virtual environment created by Plesk.

```bash
python -m venv .venv
```

Activate your environment

```bash
source .venv/bin/activate
```

Then install the requirements:

```bash
pip install -r requirements.txt
```

### Configure the `.env` file

Create the production `.env` file:

```bash
cp .env.example .env
```

Edit it:

```bash
nano .env
```

Example:

```env
DEBUG=False
SECRET_KEY=replace-this-with-a-long-random-secret-key
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

### Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic
```

If this is a fresh installation, also create an admin user:

```bash
python manage.py createsuperuser
```

### Serve static files

After running:

```bash
python manage.py collectstatic
```

the collected files will be located in:

```text
public/static
```

Make sure your Webroot points to the "public" subfolder.


### Restart the Passenger application

After changing code, settings or dependencies, restart the application.

With Passenger this can usually be done by touching a restart file:

```bash
mkdir -p tmp
touch tmp/restart.txt
```

Alternatively, use the restart button in the Plesk Python application interface if available.

### Useful maintenance commands

Update the application:

```bash
cd /var/www/vhosts/example.com/edutools
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
touch tmp/restart.txt
```

Check for deployment issues:

```bash
python manage.py check --deploy
```
