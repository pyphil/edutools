from django.shortcuts import render, redirect
import datetime
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from .models import Key
from upload.models import UploadLaufband


def dsb2(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/VheuteDSB2')
        files_vheutedsb2 = []
        for file in osfiles:
            files_vheutedsb2.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/VmorgenDSB2')
        files_vmorgendsb2 = []
        for file in osfiles:
            files_vmorgendsb2.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb2')
        files_infodsb2 = []
        for file in osfiles:
            files_infodsb2.append(file.name)

        timestamp = datetime.datetime.now().timestamp()

        return render(request, 'dsb2.html', {
            'files_vheutedsb2': files_vheutedsb2,
            'files_vmorgendsb2': files_vmorgendsb2,
            'files_infodsb2': files_infodsb2,
            'timestamp': timestamp,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb1(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/VheuteDSB1')
        files_vheutedsb1 = []
        for file in osfiles:
            files_vheutedsb1.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/VmorgenDSB1')
        files_vmorgendsb1 = []
        for file in osfiles:
            files_vmorgendsb1.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/kplan')
        files_kplan = []
        for file in osfiles:
            files_kplan.append(file.name)
        files_kplan = sorted(files_kplan)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb1')
        files_infodsb1 = []
        for file in osfiles:
            files_infodsb1.append(file.name)

        timestamp = datetime.datetime.now().timestamp()

        return render(request, 'dsb1.html', {
            'files_vheutedsb1': files_vheutedsb1,
            'files_vmorgendsb1': files_vmorgendsb1,
            'files_infodsb2': files_infodsb1,
            'files_kplan': files_kplan,
            'timestamp': timestamp,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb1_sus(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/VheuteDSB1')
        files_vheutedsb1 = []
        for file in osfiles:
            files_vheutedsb1.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/VmorgenDSB1')
        files_vmorgendsb1 = []
        for file in osfiles:
            files_vmorgendsb1.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/kplan')
        files_kplan = []
        for file in osfiles:
            files_kplan.append(file.name)
        files_kplan = sorted(files_kplan)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb1')
        files_infodsb1 = []
        for file in osfiles:
            files_infodsb1.append(file.name)

        timestamp = datetime.datetime.now().timestamp()

        try:
            laufband = UploadLaufband.objects.get(name="laufband")
            laufband_nz = laufband.text_nz
        except Exception as e:
            laufband_nz = ""
            print(e)

        return render(request, 'dsb1_sus.html', {
            'files_vheutedsb1': files_vheutedsb1,
            'files_vmorgendsb1': files_vmorgendsb1,
            'files_infodsb1': files_infodsb1,
            'files_kplan': files_kplan,
            'timestamp': timestamp,
            'laufband_nz': laufband_nz,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb2_sus(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/VheuteDSB2')
        files_vheutedsb2 = []
        for file in osfiles:
            files_vheutedsb2.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/VmorgenDSB2')
        files_vmorgendsb2 = []
        for file in osfiles:
            files_vmorgendsb2.append(file.name)

        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb2')
        files_infodsb2 = []
        for file in osfiles:
            files_infodsb2.append(file.name)

        timestamp = datetime.datetime.now().timestamp()

        try:
            laufband = UploadLaufband.objects.get(name="laufband")
            laufband_mz = laufband.text_mz
        except Exception as e:
            laufband_mz = ""
            print(e)

        return render(request, 'dsb2_sus.html', {
            'files_vheutedsb2': files_vheutedsb2,
            'files_vmorgendsb2': files_vmorgendsb2,
            'files_infodsb2': files_infodsb2,
            'timestamp': timestamp,
            'laufband_mz': laufband_mz,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb2_info(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb2')
        files_infodsb2 = []
        for file in osfiles:
            files_infodsb2.append(file.name)

        return render(request, 'dsb2_info.html', {
            'files_infodsb2': files_infodsb2,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb1_info(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        osfiles = os.scandir(settings.MEDIA_ROOT + '/infodsb1')
        files_infodsb1 = []
        for file in osfiles:
            files_infodsb1.append(file.name)

        return render(request, 'dsb1_info.html', {
            'files_infodsb1': files_infodsb1,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb_kplan(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        '''Rendert den Klausurplan auf einer separaten Seite'''
        osfiles = os.scandir(settings.MEDIA_ROOT + '/kplan')
        files_kplan = []
        for file in osfiles:
            files_kplan.append(file.name)
        files_kplan = sorted(files_kplan)

        return render(request, 'dsb_kplan.html', {
            'files_kplan': files_kplan,
            'key': key,
            }
        )
    else:
        return redirect('/')


def dsb_terminplan(request, key):
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if keycheck:
        return render(request, 'dsb_terminplan.html', {
            'key': key
            }
        )
    else:
        return redirect('/')


def dsb_media(request, key, subfolder, filename):
    """
    Serve media files with key-based access control.
    Validates the key before serving any file.
    """
    # Validate key
    db_keys = Key.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True
            break

    if not keycheck:
        raise PermissionDenied("Invalid access key")

    # Construct file path
    file_path = os.path.join(settings.MEDIA_ROOT, subfolder, filename)

    # Security: Ensure the file is within MEDIA_ROOT
    file_path = os.path.normpath(file_path)
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    if not file_path.startswith(media_root):
        raise Http404("File not found")

    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("File not found")

    # Determine content type based on file extension
    import mimetypes
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'

    # Serve the file
    return FileResponse(open(file_path, 'rb'), content_type=content_type)
