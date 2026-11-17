"""Create example boards for eduCards (demo, screenshots, onboarding).

    python manage.py educards_demo                    # demo accounts + boards (DEBUG only)
    python manage.py educards_demo --owner mueller    # boards for an existing teacher account
    python manage.py educards_demo --reset            # delete the demo boards and create them again
"""
import io
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from eduCards.models import (
    Card, CardAttachment, CardComment, CardReaction, CardsPage, CardsPageAccessToken, Category,
)
from eduCards.views import is_teacher

DEMO_TEACHER = ('demo_lehrkraft', 'Anna', 'Müller')
DEMO_COLLEAGUE = ('demo_kollege', 'Jonas', 'Schmidt')

# Each board: settings, columns and cards.
# Card tuple: (title, html content, options); "age" is minutes since creation.
BOARDS = [
    {
        'title': 'Projektwoche Klimawandel',
        'icon': '🌍', 'background': 'ocean', 'layout': CardsPage.LAYOUT_COLUMNS, 'require_approval': True,
        'description': 'Sammelt hier eure Rechercheergebnisse, Fragen und Ideen für die Präsentation am Freitag.',
        'columns': [
            ('Ursachen', '#e03131', 'Was treibt die Erderwärmung an?', [
                ('Treibhauseffekt',
                 '<p>CO<sub>2</sub>, Methan und Lachgas halten Wärme in der Atmosphäre zurück. '
                 '<strong>Seit 1850</strong> ist die CO<sub>2</sub>-Konzentration um ca. 50&nbsp;% gestiegen.</p>',
                 {'color': 'yellow', 'pinned': True, 'teacher': True, 'likes': 7, 'age': 2880,
                  'more': '<p>Quelle: Umweltbundesamt, Stand 2024</p>',
                  'comments': [('teacher', 'Super zusammengefasst! Habt ihr auch eine Grafik dazu?'),
                               ('Lea', 'Wir suchen noch eine 👍')]}),
                ('Verkehr & Energie',
                 '<ul><li>Kohlekraftwerke</li><li>Autos und Flugzeuge</li><li>Heizen mit Öl und Gas</li></ul>',
                 {'author': 'Lea & Tom', 'likes': 2, 'age': 1500}),
                ('Erklärvideo', '<p>Gutes Video für den Einstieg 👇</p>',
                 {'author': 'Noah', 'color': 'blue', 'age': 1440,
                  'link': 'https://www.youtube.com/watch?v=C9GNY-4zw5A'}),
            ]),
            ('Folgen', '#f59f00', '', [
                ('Gletscherschmelze',
                 '<p>Die Alpengletscher haben seit 1900 mehr als die Hälfte ihres Volumens verloren.</p>',
                 {'author': 'Emma', 'color': 'teal', 'likes': 3, 'age': 1300, 'image': 'gletscher.png'}),
                ('Extremwetter',
                 '<p>Hitzewellen, Dürren und Starkregen werden häufiger – z.&nbsp;B. das Ahrtal-Hochwasser 2021.</p>',
                 {'author': 'Ben', 'color': 'orange', 'likes': 1, 'age': 900}),
            ]),
            ('Lösungen', '#2f9e44', '', [
                ('Erneuerbare Energien',
                 '<p>Wind- und Solarstrom deckten 2024 schon mehr als die Hälfte des deutschen Strombedarfs.</p>',
                 {'color': 'green', 'teacher': True, 'age': 2800,
                  'link': 'https://www.umweltbundesamt.de/themen/klima-energie'}),
                ('Was wir an der Schule tun können',
                 '<p>Fahrrad-AG, Mülltrennung, Licht aus in den Pausen 💡</p>',
                 {'author': 'Klasse 8c', 'color': 'purple', 'likes': 4, 'age': 600}),
                ('Arbeitsblatt CO₂-Fußabdruck', '<p>Zum Ausfüllen in der Gruppe.</p>',
                 {'teacher': True, 'age': 2700, 'pdf': 'arbeitsblatt-co2.pdf'}),
            ]),
            ('Offene Fragen', '#1c7ed6', '', [
                ('Wie viel CO₂ verursacht ein Handy?', '<p>Herstellung vs. Nutzung – weiß das jemand?</p>',
                 {'author': 'Mia', 'color': 'pink', 'pending': True, 'age': 15}),
                ('Kipppunkte', '<p>Was passiert, wenn der Permafrost auftaut?</p>',
                 {'author': 'Finn', 'age': 120}),
            ]),
        ],
    },
    {
        'title': 'Feedback Unterrichtsreihe',
        'icon': '💬', 'background': 'lavender', 'layout': CardsPage.LAYOUT_GRID,
        'description': 'Wie fandet ihr die Reihe „Gedichte der Romantik“? Ehrliches Feedback hilft mir sehr!',
        'columns': [
            ('Das lief gut', '#2f9e44', '', [
                ('Gruppenarbeit', '<p>Die Gruppenarbeit hat Spaß gemacht und wir haben viel gelernt.</p>', {'color': 'green', 'likes': 6}),
                ('Gedichte vertonen', '<p>Das Vertonen von „Mondnacht“ war die beste Stunde! 🎵</p>', {'color': 'yellow', 'likes': 9}),
                ('Klare Arbeitsaufträge', '<p>Man wusste immer, was zu tun ist.</p>', {'likes': 2}),
            ]),
            ('Das geht besser', '#f59f00', '', [
                ('Mehr Zeit', '<p>Für die Gedichtanalyse hätten wir eine Stunde mehr gebraucht.</p>', {'color': 'orange', 'likes': 5}),
                ('Hausaufgaben', '<p>Bitte nicht mehrere Analysen in einer Woche.</p>', {'likes': 3}),
            ]),
            ('Ideen & Wünsche', '#1c7ed6', '', [
                ('Eigene Gedichte', '<p>Können wir auch selbst Gedichte schreiben und vortragen?</p>', {'color': 'blue', 'likes': 4}),
                ('Ausflug', '<p>Lesung in der Stadtbibliothek besuchen?</p>', {'color': 'pink', 'likes': 1}),
            ]),
        ],
    },
    {
        'title': 'Lektüre: Tschick',
        'icon': '📚', 'background': 'sunset', 'layout': CardsPage.LAYOUT_STREAM,
        'description': 'Lesetagebuch der 8b – haltet nach jedem Kapitel eure Gedanken fest.',
        'columns': [
            ('Kapitel 1–10', '#d6336c', '', [
                ('Erster Eindruck von Maik', '<p>Maik wirkt einsam und unsicher, aber sehr ehrlich.</p>', {'color': 'pink', 'likes': 3}),
                ('Tschick kommt in die Klasse', '<p>Alle haben Vorurteile – sein Auftritt ist trotzdem cool 😎</p>', {'likes': 5}),
            ]),
            ('Kapitel 11–20', '#7048e8', '', [
                ('Der Lada', '<p>Mit dem geklauten Lada beginnt das Abenteuer. Ist das mutig oder verantwortungslos?</p>',
                 {'color': 'purple', 'likes': 2, 'comments': [('Jonas', 'Beides! 😄')]}),
            ]),
        ],
    },
    {
        'title': 'Mathe-Fragen 7b',
        'icon': '🧮', 'background': 'forest', 'layout': CardsPage.LAYOUT_COLUMNS,
        'description': 'Stellt hier eure Fragen zu Brüchen und Prozenten – wir klären sie gemeinsam.',
        'columns': [
            ('Brüche', '#2f9e44', '', [
                ('Kürzen', '<p>Woran erkenne ich, ob ich einen Bruch noch weiter kürzen kann?</p>', {'color': 'yellow', 'likes': 4}),
                ('Brüche addieren', '<p>Warum muss ich vorher den Hauptnenner bilden?</p>', {'likes': 2}),
            ]),
            ('Prozentrechnung', '#1c7ed6', '', [
                ('Grundwert gesucht', '<p>Ich verwechsle immer Grundwert und Prozentwert 😅</p>',
                 {'color': 'blue', 'likes': 6, 'more': '<p><strong>Tipp:</strong> Der Grundwert ist immer das Ganze (100&nbsp;%).</p>'}),
            ]),
            ('Erledigt ✔', '#868e96', '', [
                ('Dezimalzahlen', '<p>Haben wir am Dienstag besprochen.</p>', {'color': 'gray'}),
            ]),
        ],
    },
]


def make_landscape_png():
    from PIL import Image, ImageDraw

    width, height = 800, 500
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    top, bottom = (120, 180, 220), (230, 240, 250)
    for y in range(height):
        mix = y / height
        draw.line([(0, y), (width, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * mix) for i in range(3)))
    draw.ellipse([560, 60, 720, 220], fill=(255, 214, 102))
    draw.polygon([(0, 500), (250, 260), (480, 500)], fill=(40, 70, 90))
    draw.polygon([(300, 500), (560, 230), (800, 500)], fill=(30, 55, 75))
    draw.polygon([(205, 305), (250, 260), (295, 305), (270, 295), (250, 310), (228, 296)], fill=(245, 248, 252))
    draw.polygon([(510, 282), (560, 230), (610, 282), (585, 272), (560, 290), (535, 272)], fill=(245, 248, 252))
    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return buffer.getvalue()


def make_worksheet_pdf():
    from PIL import Image, ImageDraw, ImageFont

    title_font = ImageFont.load_default(size=64)
    text_font = ImageFont.load_default(size=36)
    page = Image.new('RGB', (1240, 1754), 'white')
    draw = ImageDraw.Draw(page)
    draw.rectangle([0, 0, 1240, 200], fill=(47, 158, 68))
    draw.text((80, 65), 'Mein CO₂-Fußabdruck', fill='white', font=title_font)
    questions = ['Wie komme ich zur Schule?', 'Was esse ich in einer Woche?', 'Wie viele Stunden nutze ich mein Handy?',
                 'Wohin bin ich zuletzt verreist?', 'Was kann ich ändern?']
    for row, question in enumerate(questions):
        y = 280 + row * 280
        draw.text((80, y), f'{row + 1}. {question}', fill=(40, 40, 40), font=text_font)
        draw.rectangle([80, y + 60, 1160, y + 220], outline=(200, 205, 210), width=3)
    buffer = io.BytesIO()
    page.save(buffer, 'PDF')
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Legt Beispiel-Boards für eduCards an (z. B. für Vorführungen oder zum Ausprobieren).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--owner',
            help='Benutzername einer bestehenden Lehrkraft, der die Boards gehören sollen. '
                 'Ohne Angabe werden Demo-Konten angelegt (nur mit DEBUG=True).',
        )
        parser.add_argument(
            '--reset', action='store_true',
            help='Vorhandene Demo-Boards dieser Lehrkraft löschen und neu anlegen.',
        )

    def handle(self, *args, **options):
        created_accounts = []
        if options['owner']:
            owner = User.objects.filter(username=options['owner']).first()
            if owner is None:
                raise CommandError(f'Benutzer „{options["owner"]}“ existiert nicht.')
            if not is_teacher(owner):
                raise CommandError(f'„{owner.username}“ ist keine Lehrkraft (Gruppe „teachers“ oder Mitarbeiterstatus).')
            colleague = None
        else:
            if not settings.DEBUG:
                raise CommandError(
                    'Demo-Konten werden nur mit DEBUG=True angelegt. Auf einem Produktivsystem bitte '
                    '--owner <benutzername> verwenden, um die Boards einer bestehenden Lehrkraft zuzuordnen.'
                )
            owner, password = self._demo_user(*DEMO_TEACHER)
            if password:
                created_accounts.append((owner.username, password))
            colleague, password = self._demo_user(*DEMO_COLLEAGUE)
            if password:
                created_accounts.append((colleague.username, password))

        # Demo boards are recognised by title *and* description, so a teacher's own board
        # that happens to share a title is never touched.
        demo_match = Q()
        for board in BOARDS:
            demo_match |= Q(title=board['title'], description=board['description'])
        existing = CardsPage.objects.filter(demo_match, created_by=owner)
        if options['reset']:
            deleted = existing.count()
            existing.delete()
            if deleted:
                self.stdout.write(f'{deleted} vorhandene Demo-Board(s) gelöscht.')
            existing_titles = set()
        else:
            existing_titles = set(existing.values_list('title', flat=True))

        created = []
        for board in BOARDS:
            if board['title'] in existing_titles:
                self.stdout.write(f'Übersprungen (existiert bereits): {board["title"]}')
                continue
            with transaction.atomic():
                created.append(self._create_board(board, owner))

        if colleague is not None and created:
            created[0].shared_with.add(colleague)

        self._report(created, created_accounts, owner)

    # ------------------------------------------------------------------ helpers
    def _demo_user(self, username, first_name, last_name):
        group, _ = Group.objects.get_or_create(name='teachers')
        user, is_new = User.objects.get_or_create(
            username=username, defaults={'first_name': first_name, 'last_name': last_name},
        )
        password = None
        if is_new:
            password = secrets.token_urlsafe(9)
            user.set_password(password)
            user.save()
        user.groups.add(group)
        return user, password

    def _create_board(self, spec, owner):
        now = timezone.now()
        page = CardsPage.objects.create(
            title=spec['title'], icon=spec['icon'], description=spec['description'],
            background=spec['background'], layout=spec['layout'],
            require_approval=spec.get('require_approval', False), created_by=owner,
        )
        CardsPage.objects.filter(pk=page.pk).update(created=now - timedelta(days=3))
        voter = 0
        for column_index, (name, color, description, cards) in enumerate(spec['columns']):
            category = Category.objects.create(
                cards_page=page, name=name, color=color, description=description or None, order=column_index,
            )
            for card_index, (title, content, opts) in enumerate(cards):
                card = Card.objects.create(
                    category=category, title=title, content=content, order=card_index,
                    additional_info=opts.get('more', ''), link_url=opts.get('link', ''),
                    color=opts.get('color', 'white'), is_pinned=opts.get('pinned', False),
                    is_approved=not opts.get('pending', False),
                    created_by=owner if opts.get('teacher') else None,
                    author_name='' if opts.get('teacher') else opts.get('author', ''),
                    guest_key='' if opts.get('teacher') else secrets.token_hex(16),
                )
                age = timedelta(minutes=opts.get('age', 60 * (len(cards) - card_index) + 30 * column_index))
                Card.objects.filter(pk=card.pk).update(created=now - age, last_modified=now - age)

                if opts.get('image'):
                    CardAttachment.objects.create(card=card, file=ContentFile(make_landscape_png(), name=opts['image']))
                if opts.get('pdf'):
                    CardAttachment.objects.create(card=card, file=ContentFile(make_worksheet_pdf(), name=opts['pdf']))
                for _ in range(opts.get('likes', 0)):
                    voter += 1
                    CardReaction.objects.create(card=card, voter_key=f'demo-{page.pk}-{voter}')
                for comment_index, (author, text) in enumerate(opts.get('comments', [])):
                    comment = CardComment.objects.create(
                        card=card, text=text,
                        user=owner if author == 'teacher' else None,
                        author_name='' if author == 'teacher' else author,
                    )
                    CardComment.objects.filter(pk=comment.pk).update(
                        created=now - age + timedelta(minutes=20 * (comment_index + 1)))

        CardsPageAccessToken.objects.create(
            cards_page=page, token=secrets.token_urlsafe(18),
            access_level=CardsPageAccessToken.ACCESS_EDIT, created_by=owner,
        )
        return page

    def _report(self, created, accounts, owner):
        style = self.style
        if not created:
            self.stdout.write(style.WARNING('Keine neuen Boards angelegt. Mit --reset werden die Demo-Boards neu erstellt.'))
            return
        self.stdout.write(style.SUCCESS(f'{len(created)} Demo-Board(s) für „{owner.username}“ angelegt:'))
        for page in created:
            token = page.access_tokens.first()
            self.stdout.write(f'  {page.icon} {page.title}')
            self.stdout.write(f'      Board:            {reverse("eduCards:cards_page_detail", kwargs={"page_id": page.id})}')
            self.stdout.write(f'      Schüler-Zugang:   '
                              f'{reverse("eduCards:access_page_via_qr", kwargs={"page_id": page.id, "token": token.token})}')
        if accounts:
            self.stdout.write('')
            self.stdout.write(style.SUCCESS('Neue Demo-Konten (Passwort wird nur jetzt angezeigt):'))
            for username, password in accounts:
                self.stdout.write(f'  {username} / {password}')
            self.stdout.write(f'  „{created[0].title}“ ist mit {DEMO_COLLEAGUE[0]} geteilt.')
