

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
- Possibility to link a digital notice board/representation plan view (integration of the djDSB app into the collection is planned for the future)

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
- Möglichkeit ein Digitales Schwarzes Brett/Vertretungsplanansicht zu verlinken (Einbindung der App djDSB in die Sammlung ist für die Zukunft geplant)

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

## Using local_settings.py
The ```file local_settings.py``` in /edutools_site/ is used in settings.py if present in order to hide your secret key and email settings. Use the template ```local_settings_template.py``` to create your settings file.
