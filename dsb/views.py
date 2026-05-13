from django.shortcuts import render, redirect
from django.contrib import messages
import datetime
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from .models import Key
from .models import DsbName
from .forms import KeyForm, DsbNameForm, UploadKeyForm
from upload.models import UploadLaufband, UploadKey


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
            'dsb1_name': get_dsb_name("dsb1"),
            'dsb2_name': get_dsb_name("dsb2"),
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
            'dsb1_name': get_dsb_name("dsb1"),
            'dsb2_name': get_dsb_name("dsb2"),
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
            'dsb1_name': get_dsb_name("dsb1"),
            'dsb2_name': get_dsb_name("dsb2"),
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
            'dsb1_name': get_dsb_name("dsb1"),
            'dsb2_name': get_dsb_name("dsb2"),
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
            'dsb2_name': get_dsb_name("dsb2"),
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
            'dsb1_name': get_dsb_name("dsb1"),
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


def dsb_admin(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/')

    dsb_name, _ = DsbName.objects.get_or_create(
        pk=1,
        defaults={"dsb1": "", "dsb2": ""},
    )
    keys = Key.objects.order_by('key')
    upload_keys = UploadKey.objects.order_by('key')
    status_message = None
    key_form = KeyForm()
    uploadkey_form = UploadKeyForm()
    dsbname_form = DsbNameForm(instance=dsb_name)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_dsbname':
            dsbname_form = DsbNameForm(request.POST, instance=dsb_name)
            if dsbname_form.is_valid():
                dsbname_form.save()
                messages.success(request, 'DSB-Bezeichnungen wurden gespeichert.')
                return redirect('dsb_admin')
            else:
                status_message = 'Bitte gültige DSB-Bezeichnungen eingeben.'

        elif action == 'add_key':
            key_form = KeyForm(request.POST)
            if key_form.is_valid():
                key_form.save()
                messages.success(request, 'Neuer Zugangsschlüssel wurde hinzugefügt.')
                return redirect('dsb_admin')
            else:
                status_message = 'Bitte einen gültigen Zugangsschlüssel eingeben.'

        elif action == 'edit_key':
            key_id = request.POST.get('key_id')
            if key_id:
                try:
                    key_obj = Key.objects.get(pk=key_id)
                    key_form = KeyForm(request.POST, instance=key_obj)
                    if key_form.is_valid():
                        key_form.save()
                        messages.success(request, 'Zugangsschlüssel wurde aktualisiert.')
                        return redirect('dsb_admin')
                    else:
                        status_message = 'Bitte einen gültigen Zugangsschlüssel eingeben.'
                except Key.DoesNotExist:
                    status_message = 'Der ausgewählte Zugangsschlüssel wurde nicht gefunden.'
            else:
                status_message = 'Kein Zugangsschlüssel ausgewählt.'

        elif action == 'delete_key':
            key_id = request.POST.get('key_id')
            if key_id:
                Key.objects.filter(pk=key_id).delete()
                messages.success(request, 'Zugangsschlüssel wurde entfernt.')
                return redirect('dsb_admin')
            else:
                status_message = 'Kein Zugangsschlüssel ausgewählt.'

        elif action == 'add_uploadkey':
            uploadkey_form = UploadKeyForm(request.POST)
            if uploadkey_form.is_valid():
                uploadkey_form.save()
                messages.success(request, 'Neuer Upload-Schlüssel wurde hinzugefügt.')
                return redirect('dsb_admin')
            else:
                status_message = 'Bitte einen gültigen Upload-Schlüssel eingeben.'

        elif action == 'edit_uploadkey':
            uploadkey_id = request.POST.get('uploadkey_id')
            if uploadkey_id:
                try:
                    uploadkey_obj = UploadKey.objects.get(pk=uploadkey_id)
                    uploadkey_form = UploadKeyForm(request.POST, instance=uploadkey_obj)
                    if uploadkey_form.is_valid():
                        uploadkey_form.save()
                        messages.success(request, 'Upload-Schlüssel wurde aktualisiert.')
                        return redirect('dsb_admin')
                    else:
                        status_message = 'Bitte einen gültigen Upload-Schlüssel eingeben.'
                except UploadKey.DoesNotExist:
                    status_message = 'Der ausgewählte Upload-Schlüssel wurde nicht gefunden.'
            else:
                status_message = 'Kein Upload-Schlüssel ausgewählt.'

        elif action == 'delete_uploadkey':
            uploadkey_id = request.POST.get('uploadkey_id')
            if uploadkey_id:
                UploadKey.objects.filter(pk=uploadkey_id).delete()
                messages.success(request, 'Upload-Schlüssel wurde entfernt.')
                return redirect('dsb_admin')
            else:
                status_message = 'Kein Upload-Schlüssel ausgewählt.'

        keys = Key.objects.order_by('key')
        upload_keys = UploadKey.objects.order_by('key')
        if action not in ['add_key', 'edit_key', 'delete_key']:
            key_form = KeyForm()
        if action not in ['add_uploadkey', 'edit_uploadkey', 'delete_uploadkey']:
            uploadkey_form = UploadKeyForm()
        if action != 'update_dsbname':
            dsbname_form = DsbNameForm(instance=dsb_name)

    return render(request, 'dsb_admin.html', {
        'dsbname_form': dsbname_form,
        'key_form': key_form,
        'uploadkey_form': uploadkey_form,
        'keys': keys,
        'upload_keys': upload_keys,
        'status_message': status_message,
    })


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


def get_dsb_name(dsb):
    dsb_name, created = DsbName.objects.get_or_create(
        pk=1,
        defaults={"dsb1": "", "dsb2": ""},
    )

    if dsb == "dsb1":
        if dsb_name.dsb1:
            return f"({dsb_name.dsb1})"
    if dsb == "dsb2":
        if dsb_name.dsb2:
            return f"({dsb_name.dsb2})"
    return ""
