"""
Erzeugt Beispieldaten für die lokale Entwicklung.

    python manage.py seed_demo            # Beispieldaten anlegen (idempotent)
    python manage.py seed_demo --flush    # vorher alle Inhaltsdaten der Apps löschen

Angelegte Test-Logins (nur für die lokale Entwicklung!):
    admin  / demo1234   (Superuser)
    mueller, schmidt, weber / demo1234   (Gruppe "teachers")
    bibliothek / demo1234   (Gruppe "library_admin")
    termine    / demo1234   (Gruppe "appointment_admin")
    angebote   / demo1234   (Gruppe "activity_admin")
"""
import random
import uuid
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
from activity.models import Activity, ActivityBlock, ActivitySetting, BookedActivity
from appointment.models import Appointment, AppointmentMail, AppointmentSetting
from buchungstool.models import FAQ, Booking, Category, Room
from buchungstool_settings.models import Setting
from devicelist.models import Device, DevicelistEntry, Status
from dsb.models import DsbName, Key
from edutools_home.models import EdutoolsSetting
from library_manager.models import (
    InventoryItem, LibraryBorrowedItem, LibraryCategoryShelfmark, LibraryLocation, LibraryStatus,
)
from mkr.models import Fach, Kompetenzkarte
from upload.models import UploadKey, UploadLaufband
from userlist.models import Userlist
from WLANCodesWebApp.models import AllowedEmail, Code, Config, Student

PASSWORD = 'demo1234'

FIRSTNAMES = ['Lena', 'Jonas', 'Mia', 'Paul', 'Emma', 'Ben', 'Hannah', 'Luca', 'Sophie', 'Finn',
              'Lea', 'Noah', 'Marie', 'Elias', 'Emilia', 'Leon', 'Clara', 'Anton', 'Ida', 'Theo']
SURNAMES = ['Becker', 'Hoffmann', 'Schulz', 'Koch', 'Richter', 'Klein', 'Wolf', 'Neumann',
            'Schwarz', 'Braun', 'Zimmermann', 'Krüger', 'Hartmann', 'Lange', 'Werner']
GROUPS = ['5a', '5b', '6a', '6c', '7b', '8a', '9c', '10a', 'EF', 'Q1']

TEACHERS = [
    ('mueller', 'Anna', 'Müller', 'MÜL'),
    ('schmidt', 'Thomas', 'Schmidt', 'SMT'),
    ('weber', 'Julia', 'Weber', 'WEB'),
]


def school_days(start, count):
    """Liefert `count` Werktage ab `start` (inkl.)."""
    days, d = [], start
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


class Command(BaseCommand):
    help = 'Erzeugt Beispieldaten (Benutzer, Räume, Buchungen, Bibliothek, Termine, ...) für die Entwicklung.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Vorher alle Inhaltsdaten der Apps löschen (Benutzer bleiben erhalten).')
        parser.add_argument('--seed', type=int, default=42, help='Zufalls-Seed für reproduzierbare Daten.')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo ist nur mit DEBUG=True erlaubt.')
        random.seed(options['seed'])
        self.today = timezone.localdate()
        self.monday = self.today - timedelta(days=self.today.weekday())

        with transaction.atomic():
            if options['flush']:
                self.flush()
            self.users()
            self.settings()
            self.rooms_and_bookings()
            self.devicelist()
            self.wlan()
            self.library()
            self.appointments()
            self.activities()
            self.mkr()
            self.misc()
        self.stdout.write(self.style.SUCCESS('Beispieldaten angelegt. Login z.B. admin / ' + PASSWORD))

    def log(self, msg):
        self.stdout.write('  ' + msg)

    # ------------------------------------------------------------------
    def flush(self):
        for model in [LibraryBorrowedItem, InventoryItem, LibraryCategoryShelfmark, LibraryLocation,
                      LibraryStatus, DevicelistEntry, Booking, Userlist, Room, Category, FAQ,
                      BookedActivity, Activity, ActivityBlock, ActivitySetting, Appointment,
                      AppointmentMail, AppointmentSetting, Kompetenzkarte, Fach, Student, Code,
                      Config, AllowedEmail, UploadLaufband, UploadKey, DsbName, Key]:
            model.objects.all().delete()
        self.log('Bestehende Inhaltsdaten gelöscht.')

    def users(self):
        groups = {n: Group.objects.get_or_create(name=n)[0]
                  for n in ['teachers', 'library_admin', 'library_assistant',
                            'appointment_admin', 'activity_admin']}

        def make(username, first, last, *, superuser=False, group_names=()):
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.first_name, user.last_name = first, last
                user.email = f'{username}@schule.example'
                user.is_staff = user.is_superuser = superuser
                user.set_password(PASSWORD)
                user.save()
            for g in group_names:
                user.groups.add(groups[g])
            return user

        make('admin', 'Admin', 'eduTools', superuser=True)
        for username, first, last, abbr in TEACHERS:
            user = make(username, first, last, group_names=['teachers'])
            UserProfile.objects.get_or_create(user=user, defaults={'abbr': abbr, 'email': user.email})
        make('bibliothek', 'Bea', 'Bücher', group_names=['library_admin', 'teachers'])
        make('termine', 'Tim', 'Termin', group_names=['appointment_admin'])
        make('angebote', 'Anja', 'Angebot', group_names=['activity_admin'])
        self.log(f'{User.objects.count()} Benutzer.')

    def settings(self):
        EdutoolsSetting.objects.get_or_create(name='settings', defaults={
            'login_hint': 'Demo-Login: admin / ' + PASSWORD,
            'legal_notice': 'https://schule.example/impressum',
            'privacy_policy': 'https://schule.example/datenschutz',
        })
        Setting.objects.get_or_create(name='settings', defaults={
            'institution': 'Demo-Gesamtschule',
            'email_to': 'it@schule.example',
            'noreply_mail': 'noreply@schule.example',
            'dsb_link': 'https://schule.example/dsb',
            'mkr_link': 'https://medienkompetenzrahmen.nrw',
            'info_frontpage': '<p>Willkommen im <strong>Demo-Buchungstool</strong>. '
                              'Alle Daten sind Beispieldaten.</p>',
        })
        self.log('Einstellungen.')

    def rooms_and_bookings(self):
        if Room.objects.exists():
            self.log('Räume existieren bereits – übersprungen.')
            return
        cats = [Category.objects.create(name=n, position=i + 1, color=c, column_break=(i == 1))
                for i, (n, c) in enumerate([('iPad-Koffer', '#d6eaf8'), ('Computerräume', '#d5f5e3'),
                                            ('Fachräume', '#fdebd0')])]
        rooms_def = [
            (cats[0], 'K1', 'Koffer 1', 'iPad-Koffer Gebäude A', '16'),
            (cats[0], 'K2', 'Koffer 2', 'iPad-Koffer Gebäude B', '16'),
            (cats[1], 'PC1', 'Raum 104', 'Computerraum 1', ''),
            (cats[1], 'PC2', 'Raum 210', 'Computerraum 2', ''),
            (cats[2], 'NW1', 'Raum 301', 'Physik mit Beamer', ''),
            (cats[2], 'AULA', 'Aula', 'Aula mit Bühnentechnik', ''),
        ]
        rooms = []
        pos = 1
        for cat in cats:
            members = [r for r in rooms_def if r[0] is cat]
            for i, (_, short, name, desc, count) in enumerate(members):
                rooms.append(Room.objects.create(
                    category=cat, short_name=short, room=name, description=desc, device_count=count,
                    position=pos, is_first_of_category=(i == 0), is_last_of_category=(i == len(members) - 1)))
                pos += 1
        rooms[0].alert = '<p>Ladekabel von iPad 07 fehlt.</p>'
        rooms[0].save()

        FAQ.objects.create(question='Wie buche ich einen iPad-Koffer?',
                           answer='<p>Raum wählen, freie Stunde anklicken und Lerngruppe eintragen.</p>')
        FAQ.objects.create(question='Wie melde ich einen Schaden?',
                           answer='<p>Über die Geräteliste des Raums einen neuen Eintrag anlegen.</p>')

        abbrs = [t[3] for t in TEACHERS]
        days = school_days(self.monday - timedelta(days=7), 15)  # letzte, diese und nächste Woche
        count = 0
        for room in rooms:
            for day in days:
                for std in random.sample(range(1, 8), k=random.randint(1, 3)):
                    b = Booking(room=room.short_name, krzl=random.choice(abbrs),
                                lerngruppe=random.choice(GROUPS), datum=day, stunde=std)
                    if room.device_count:
                        names = random.sample(FIRSTNAMES, k=8)
                        for n, first in enumerate(names, start=1):
                            setattr(b, f'iPad_{n:02d}', f'{first} {random.choice(SURNAMES)}')
                            setattr(b, f'pen_{n:02d}', random.choice(['', 'x']))
                    b.save()
                    count += 1
        # eine Serienbuchung: jeden Montag 3. Stunde in K2
        series = uuid.uuid4().hex
        for w in range(4):
            d = self.monday + timedelta(weeks=w)
            Booking.objects.filter(room='K2', datum=d, stunde=3).delete()
            Booking.objects.create(room='K2', krzl='WEB', lerngruppe='Informatik 8a',
                                   datum=d, stunde=3, series_id=series)
            count += 1
        # Einträge für die heutige Nutzerliste
        for b in Booking.objects.filter(datum=self.today, room__in=['K1', 'K2']):
            Userlist.objects.create(short_name=b.room, lerngruppe=b.lerngruppe, datum=b.datum,
                                    stunde=b.stunde, krzl=b.krzl, created=timezone.now())
        self.log(f'{len(rooms)} Räume, {count} Buchungen.')

    def devicelist(self):
        # entspricht buchungstool.views.first_run()
        for i in range(1, 17):
            Device.objects.get_or_create(dbname=f'iPad_{i:02d}', defaults={'device': f'iPad {i:02d}', 'position': i})
            Device.objects.get_or_create(dbname=f'pen_{i:02d}', defaults={'device': f'Stift {i:02d}', 'position': i})
        statuses = {}
        for s, c in [('offen', 'text-danger'), ('in Bearbeitung', 'text-warning'),
                     ('gelöst', 'text-success'), ('irreparabel', 'text-danger')]:
            statuses[s] = Status.objects.get_or_create(status=s, defaults={'color': c})[0]
        if DevicelistEntry.objects.exists() or not Room.objects.filter(short_name='K1').exists():
            return
        rooms = list(Room.objects.filter(short_name__in=['K1', 'K2']))
        problems = ['Display gesprungen', 'Akku lädt nicht', 'Stift koppelt nicht',
                    'Hülle beschädigt', 'WLAN-Verbindung bricht ab', 'Ladekabel fehlt']
        for i, text in enumerate(problems):
            status = random.choice(list(statuses.values()))
            DevicelistEntry.objects.create(
                room=random.choice(rooms), device=Device.objects.get(dbname=f'iPad_{i + 3:02d}'),
                datum=self.today - timedelta(days=random.randint(1, 40)), stunde=random.randint(1, 7),
                beschreibung=text, krzl=random.choice(TEACHERS)[3], status=status,
                behoben='WEB' if status.status == 'gelöst' else '')
        self.log(f'{DevicelistEntry.objects.count()} Schadensmeldungen.')

    def wlan(self):
        for name, setting, text in [
            ('noreply-mail', 'noreply@schule.example', None),
            ('mail_text', '', 'Hallo #NAME#,\n\ndein WLAN-Code lautet: #CODE#\n\nViele Grüße'),
            ('lnk_controller', 'https://wlan-controller.schule.example', None),
            ('access', 'demo-access-key', None),
        ]:
            Config.objects.get_or_create(name=name, defaults={'setting': setting, 'text': text})
        AllowedEmail.objects.get_or_create(school='Demo-Gesamtschule',
                                           defaults={'emails': '@schule.example'})
        if Code.objects.exists():
            return
        for typ, dur, n in [('h', 1, 20), ('d', 1, 10), ('y', 1, 30)]:
            for _ in range(n):
                Code.objects.create(code=f'{random.randint(0, 99999):05d}-{random.randint(0, 99999):05d}',
                                    type=typ, duration=dur)
        for i in range(12):
            first, last = random.choice(FIRSTNAMES), random.choice(SURNAMES)
            Student.objects.create(name=last, firstname=first, group=random.choice(GROUPS)[:3],
                                   email=f'{first.lower()}{i}@schule.example'[:30],
                                   date=timezone.now() - timedelta(days=random.randint(0, 60)) if i % 2 else None,
                                   code=f'{random.randint(0, 99999):05d}-{random.randint(0, 99999):05d}' if i % 2 else None)
        self.log(f'{Code.objects.count()} WLAN-Codes, {Student.objects.count()} Schüler:innen.')

    def library(self):
        if InventoryItem.objects.exists():
            return
        cats = [LibraryCategoryShelfmark.objects.create(category=c, shelfmark=s) for c, s in
                [('Jugendbuch', 'JB'), ('Sachbuch', 'SB'), ('Klassiker', 'KL'), ('Comic', 'CO')]]
        locs = [LibraryLocation.objects.create(name=n) for n in ['Bibliothek', 'Lehrerzimmer', 'Magazin']]
        stats = {n: LibraryStatus.objects.create(name=n) for n in ['verfügbar', 'beschädigt', 'verloren']}
        books = [
            ('Michael Ende', 'Momo', 2), ('Cornelia Funke', 'Tintenherz', 0), ('Kirsten Boie', 'Ritter Trenk', 0),
            ('Wolfgang Herrndorf', 'Tschick', 0), ('Andreas Steinhöfel', 'Rico, Oskar und die Tieferschatten', 0),
            ('Johann Wolfgang von Goethe', 'Faust I', 2), ('Friedrich Schiller', 'Die Räuber', 2),
            ('Theodor Fontane', 'Effi Briest', 2), ('Stephen Hawking', 'Eine kurze Geschichte der Zeit', 1),
            ('Bill Bryson', 'Eine kurze Geschichte von fast allem', 1), ('Hergé', 'Tim und Struppi: Reiseziel Mond', 3),
            ('René Goscinny', 'Asterix der Gallier', 3), ('Erich Kästner', 'Emil und die Detektive', 0),
            ('Otfried Preußler', 'Krabat', 0), ('Mirjam Pressler', 'Bitterschokolade', 0),
        ]
        items = []
        for n, (author, title, cat) in enumerate(books, start=1):
            items.append(InventoryItem.objects.create(
                author=author, title=title, category_shelfmark=cats[cat], inventory_number=n,
                location=locs[0] if n % 5 else locs[2],
                status=stats['beschädigt'] if n == 7 else stats['verfügbar'],
                notes='Einband lose' if n == 7 else ''))
        for i, item in enumerate(random.sample(items, 6)):
            borrowed = self.today - timedelta(days=random.randint(5, 40))
            LibraryBorrowedItem.objects.create(
                first_name=random.choice(FIRSTNAMES), surname=random.choice(SURNAMES),
                school_class=random.choice(GROUPS), book=item, borrowing_date=borrowed,
                return_date=borrowed + timedelta(days=21))  # teils überfällig
        self.log(f'{len(items)} Bücher, 6 Ausleihen.')

    def appointments(self):
        AppointmentSetting.objects.get_or_create(title='Anmeldung Jahrgang 5', defaults={
            'description': 'Bitte wählen Sie einen Termin für das Anmeldegespräch.', 'show_empty_days': True})
        AppointmentMail.objects.get_or_create(id=1, defaults={
            'mail_text': 'Guten Tag,\n\nIhr Termin für #KIND# ist am #DATUM# um #UHRZEIT#.\n\nMit freundlichen Grüßen',
            'mail_text_reminder': 'Guten Tag,\n\nwir erinnern an Ihren Termin für #KIND# am #DATUM# um #UHRZEIT#.'})
        if Appointment.objects.exists():
            return
        primaries = ['GS Am Park', 'GS Lindenweg', 'Marienschule', 'GS Sonnenhügel']
        for day in school_days(self.today + timedelta(days=1), 3):
            for slot in range(12):
                t = (datetime.combine(day, time(14, 0)) + timedelta(minutes=20 * slot)).time()
                a = Appointment(date=day, time=t)
                if random.random() < 0.4:
                    first, last = random.choice(FIRSTNAMES), random.choice(SURNAMES)
                    a.student_name = f'{first} {last}'
                    a.parents_name = f'Familie {last}'
                    a.primary_school = random.choice(primaries)
                    a.email = f'{last.lower()}@example.org'
                    a.phone = f'0201 {random.randint(100000, 999999)}'
                a.save()
        self.log(f'{Appointment.objects.count()} Termine.')

    def activities(self):
        ActivitySetting.objects.get_or_create(id=1, defaults={'title': 'Tag der offenen Tür'})
        if ActivityBlock.objects.exists():
            return
        blocks = [ActivityBlock.objects.create(name=n, order=i) for i, n in
                  enumerate(['Block 1 (9:00–10:00)', 'Block 2 (10:30–11:30)', 'Block 3 (12:00–13:00)'])]
        acts = [Activity.objects.create(name=n, order=i) for i, n in enumerate(
            ['Chemie-Experimente', 'Roboter programmieren', 'Schnupperunterricht Englisch',
             'Kunstwerkstatt', 'Sport-Parcours', 'Schulführung'])]
        for _ in range(25):
            last = random.choice(SURNAMES)
            BookedActivity.objects.create(block=random.choice(blocks), activity=random.choice(acts),
                                          student_name=f'{random.choice(FIRSTNAMES)} {last}',
                                          parents_name=f'Familie {last}')
        self.log(f'{len(blocks)} Blöcke, {len(acts)} Angebote, 25 Anmeldungen.')

    def mkr(self):
        if Kompetenzkarte.objects.exists():
            return
        faecher = {n: Fach.objects.create(fach=n) for n in
                   ['Deutsch', 'Mathematik', 'Informatik', 'Englisch', 'Politik', 'Kunst']}
        users = list(User.objects.filter(groups__name='teachers'))
        cards = [
            ('12', 'Informatik', '05', 'Einführung in iPad und Apps'),
            ('14', 'Informatik', '06', 'Sichere Passwörter'),
            ('21', 'Deutsch', '06', 'Recherche für ein Referat'),
            ('24', 'Politik', '08', 'Fake News erkennen'),
            ('34', 'Politik', '07', 'Cybermobbing – was tun?'),
            ('41', 'Englisch', '09', 'Erklärvideo erstellen'),
            ('42', 'Kunst', '07', 'Bildbearbeitung'),
            ('44', 'Deutsch', '09', 'Urheberrecht und Bildrechte'),
            ('53', 'Deutsch', '10', 'Selbstdarstellung in sozialen Medien'),
            ('63', 'Informatik', '08', 'Programmieren mit Scratch'),
            ('62', 'Mathematik', '11', 'Algorithmen in der Tabellenkalkulation'),
        ]
        for kat, fach, jgst, vorhaben in cards:
            user = random.choice(users) if users else None
            Kompetenzkarte.objects.create(
                kategorie=kat, fach=faecher[fach], jgst=jgst, vorhaben=vorhaben,
                info=f'Unterrichtsvorhaben „{vorhaben}“ (ca. 4 Stunden).',
                medienkompetenz='Die SuS können digitale Werkzeuge zielgerichtet einsetzen.',
                vorwissen_sus='Grundlegende Bedienung des iPads',
                technik='iPad-Koffer, Beamer', medienkenntnisse_lul='Grundkenntnisse',
                alle_teil=random.choice('01'), pflicht_empf=random.choice('01'),
                durchf_planung=random.choice('01'), user=user, last_user=user)
        self.log(f'{len(cards)} Kompetenzkarten.')

    def misc(self):
        UploadKey.objects.get_or_create(key='demo-upload-key')
        Key.objects.get_or_create(key='demo-dsb-key')
        DsbName.objects.get_or_create(id=1, defaults={'dsb1': 'Vertretungsplan heute',
                                                      'dsb2': 'Vertretungsplan morgen'})
        UploadLaufband.objects.get_or_create(name='laufband', defaults={
            'text_nz': 'Willkommen an der Demo-Gesamtschule!',
            'text_mz': '+++ Elternsprechtag am Donnerstag +++'})
        self.log('DSB/Upload-Schlüssel.')
