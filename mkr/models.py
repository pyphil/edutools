from django.db import models
from django.contrib.auth.models import User


class Fach(models.Model):
    fach = models.CharField(max_length=50)

    def __str__(self):
        return self.fach

    class Meta:
        verbose_name_plural = 'Fächer'
        ordering = ['fach']


class Kompetenzkarte(models.Model):
    KATEGORIE_CHOICES = [
        ('11', '1.1 Medienausstattung'),
        ('12', '1.2 Digitale Werkzeuge'),
        ('13', '1.3 Datenorganisation'),
        ('14', '1.4 Datenschutz und Informationssicherheit'),
        ('21', '2.1 Informationsrecherche'),
        ('22', '2.2 Informationsauswertung'),
        ('23', '2.3 Informationsbewertung'),
        ('24', '2.4 Informationskritik'),
        ('31', '3.1 Kommunikations- und Kooperationsprozesse'),
        ('32', '3.2 Kommunikations- und Kooperationsregeln'),
        ('33', '3.3 Kommunikation und Kooperation in der Gesellschaft'),
        ('34', '3.4 Cybergewalt und -kriminalität'),
        ('41', '4.1 Medienproduktion und Präsentation'),
        ('42', '4.2 Gestaltungsmittel'),
        ('43', '4.3 Quellendokumentation'),
        ('44', '4.4 Rechtliche Grundlagen'),
        ('51', '5.1 Medienanalyse'),
        ('52', '5.2 Meinungsbildung'),
        ('53', '5.3 Identitätsbildung'),
        ('54', '5.4 Selbstregulierte Mediennutzung'),
        ('61', '6.1 Prinzipien der digitalen Welt'),
        ('62', '6.2 Algorithmen erkennen'),
        ('63', '6.3 Modellieren und Programmieren'),
        ('64', '6.4 Bedeutung von Algorithmen'),
    ]
    kategorie = models.CharField(max_length=2, choices=KATEGORIE_CHOICES)
    fach = models.ForeignKey(Fach, on_delete=models.PROTECT)
    JGST_CHOICES = [
        ('05', 'Jgst. 5'),
        ('06', 'Jgst. 6'),
        ('07', 'Jgst. 7'),
        ('08', 'Jgst. 8'),
        ('09', 'Jgst. 9'),
        ('10', 'Jgst. 10'),
        ('11', 'Jgst. EF'),
        ('12', 'Jgst. Q1'),
        ('13', 'Jgst. Q2'),
        ('JG', 'mehrere Jgst.'),
    ]
    jgst = models.CharField(max_length=2, choices=JGST_CHOICES)
    vorhaben = models.CharField(max_length=200)
    info = models.CharField(max_length=400)
    medienkompetenz = models.CharField(max_length=400)
    vorwissen_sus = models.CharField(max_length=400)
    technik = models.CharField(max_length=400)
    medienkenntnisse_lul = models.CharField(max_length=400)
    ALLE_TEIL_CHOICES = [
        ('0', 'ist für alle '),
        ('1', 'ist für eine Teilgruppe'),
    ]
    alle_teil = models.CharField(max_length=1, choices=ALLE_TEIL_CHOICES)
    PFLICHT_EMPF_CHOICES = [
        ('0', 'ist Pflicht'),
        ('1', 'ist Empfehlung'),
    ]
    pflicht_empf = models.CharField(max_length=1, choices=PFLICHT_EMPF_CHOICES)
    DURCHF_PLANUNG_CHOICES = [
        ('0', 'wird durchgeführt'),
        ('1', 'wird geplant/erprobt'),
    ]
    durchf_planung = models.CharField(max_length=1, choices=DURCHF_PLANUNG_CHOICES)
    download = models.FileField(null=True, blank=True, upload_to="downloads/")
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='edited_datasets', null=True, blank=True)
    changed = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Kompetenzkarten'
        ordering = ['kategorie', 'fach', 'jgst']
