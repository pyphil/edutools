from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from buchungstool.models import Booking, Room
from buchungstool_settings.models import Setting
from .models import DevicelistEntry, Device, Status
from .forms import DevicelistEntryForm, DevicelistEntryFormLoggedIn
from django.core.mail import send_mail
from threading import Thread
from django.db.models import Q


def is_teacher(user):
    return user.is_staff or user.groups.filter(name='teachers').exists()


@login_required
@user_passes_test(is_teacher)
def devicelist(request, room, date, std, entry_id):
    devices = Device.objects.all()
    obj = DevicelistEntry.objects.filter(room__short_name=room)
    iPads_with_entry = []
    for i in obj:
        iPads_with_entry.append(i.device)
    context = {
        'room': room,
        'date': date,
        'std': std,
        'devices': devices,
        'iPads_with_entry': iPads_with_entry,
        'devicelist': obj,
        'entry_id': entry_id,
    }
    return render(request, 'devicelist.html', context)


@login_required
@user_passes_test(is_teacher)
def devicelist_all(request):
    if request.GET.get('filter_status') and request.GET.get('filter_status') != "alle":
        filter_status = request.GET.get('filter_status')
        obj = DevicelistEntry.objects.filter(status__status=filter_status).order_by('room', 'device')
    else:
        obj = DevicelistEntry.objects.all().order_by('room', 'device')
        filter_status = ""
    if request.GET.get('filter_room') and request.GET.get('filter_room') != "alle":
        filter_room = int(request.GET.get('filter_room'))
        obj = obj.filter(room__id=filter_room).order_by('room', 'device')
    else:
        filter_room = ""
    if request.GET.get('textfilter'):
        try:
            idfilter = int(request.GET.get('textfilter'))
        except ValueError:
            idfilter = None

        textfilter = request.GET.get('textfilter')
        obj = obj.filter(
            Q(beschreibung__icontains=textfilter) |
            Q(id=idfilter) |
            Q(room__short_name__icontains=textfilter) |
            Q(krzl__icontains=textfilter) |
            Q(room__room__icontains=textfilter)
        )
    if request.GET.get('sortdate'):
        sortdate = request.GET.get('sortdate')
        if sortdate == "asc":
            obj = obj.order_by('datum', 'stunde')
        else:
            obj = obj.order_by('-datum', '-stunde')
    else:
        obj = obj.order_by('-datum', '-stunde')

    status = Status.objects.all()
    options = []
    options.append('alle')
    for s in status:
        options.append(s.status)

    room_obj = Room.objects.all()
    rooms = []
    rooms.append('alle')
    for room in room_obj:
        rooms.append(room)

    if request.GET.get('textfilter'):
        textfilter = request.GET.get('textfilter')
    else:
        textfilter = ""

    if request.GET.get('sortdate'):
        sortdate = request.GET.get('sortdate')
    else:
        sortdate = ""

    context = {
        'devicelist': obj,
        'options': options,
        'rooms': rooms,
        'filter_status': filter_status,
        'filter_room': filter_room,
        'textfilter': textfilter,
        'sortdate': sortdate,
    }
    return render(request, 'devicelist_all.html', context)


@login_required
@user_passes_test(is_teacher)
def devicelistEntry(request, id, room, date, std, entry_id):
    obj = get_object_or_404(DevicelistEntry, id=id)
    if request.method == "GET":
        # Update -> load instance
        if request.user.is_staff:
            f = DevicelistEntryFormLoggedIn(instance=obj)
        else:
            f = DevicelistEntryForm(instance=obj)
    if request.method == "POST":
        if request.POST.get('save'):
            if request.user.is_staff:
                f = DevicelistEntryFormLoggedIn(request.POST, instance=obj)
            else:
                f = DevicelistEntryForm(request.POST, instance=obj)
            if f.is_valid():
                koffer = get_object_or_404(Room, id=int(request.POST.get('room')))
                device = Device.objects.get(id=int(request.POST.get('device')))
                if request.user.is_staff:
                    status = Status.objects.get(id=int(request.POST.get('status')))
                else:
                    status = request.POST.get('status')
                f.save()
                if request.POST.get('behoben'):
                    bearbeitet_von = request.POST.get('behoben')
                else:
                    bearbeitet_von = ""
                mail_text = (
                    "ID: " + str(obj.id) + "\n" +
                    "Datum: " + request.POST.get('datum') + "\n" +
                    "Stunde: " + request.POST.get('stunde') + "\n" +
                    "Standort/Koffer: " + koffer.short_name + "\n" +
                    "Gerät: " + str(device) + "\n" +
                    "Kürzel: " + request.POST.get('krzl') + "\n" +
                    "Beschreibung: " + request.POST.get('beschreibung') + "\n" +
                    "Status: " + str(status) + "\n" +
                    "Bearbeitet von: " + bearbeitet_von
                )
                subject = f'Support Ticket {str(obj.id)} Update: {str(status)}'

                if request.POST.get('email_to_second'):
                    email_to_second = request.POST.get('email_to_second')
                else:
                    email_to_second = ""

                thread = MailThread(subject, mail_text, email_to_second)
                thread.start()

                if request.POST.get('devicelist_all') == "True":
                    return redirect(reverse('devicelist_all') + "?" + request.GET.urlencode())
                else:
                    return redirect('devicelist', room=room, date=date, std=std, entry_id=entry_id)

        elif request.POST.get('delete'):
            koffer = get_object_or_404(Room, id=int(request.POST.get('room')))
            device = Device.objects.get(id=int(request.POST.get('device')))
            status = request.POST.get('status')
            if request.user.is_staff:
                status = Status.objects.get(id=int(request.POST.get('status')))
            else:
                status = request.POST.get('status')
            mail_text = (
                    "Folgende Schaden- oder Problemmeldung wurde gelöscht:\n\n" +
                    "ID: " + str(obj.id) + "\n" +
                    "Datum: " + request.POST.get('datum') + "\n" +
                    "Stunde: " + request.POST.get('stunde') + "\n" +
                    "Standort/Koffer: " + koffer.short_name + "\n" +
                    "Gerät: " + str(device) + "\n" +
                    "Kürzel: " + request.POST.get('krzl') + "\n" +
                    "Beschreibung: " + request.POST.get('beschreibung') + "\n" +
                    "Status: " + str(status)
                )

            email_to_second = ""

            subject = f'Support Ticket {str(obj.id)} gelöscht'
            thread = MailThread(subject, mail_text, email_to_second)
            thread.start()
            obj.delete()
            # Return to devicelist_all if coming from there -> use url parameter
            if request.POST.get('devicelist_all'):
                return redirect('devicelist_all')
            else:
                return redirect('devicelist', room=obj.room, date=obj.datum, std=obj.stunde, entry_id=entry_id)
        else:
            return redirect('devicelist', room=obj.room, date=obj.datum, std=obj.stunde, entry_id=entry_id)

    context = {
        'room': room,
        'devicelist': f,
        'date': date,
        'std': std,
        'support_id': id,
        'devicelist_all': request.GET.get('devicelist_all'),
    }

    return render(request, 'devicelistEntry.html', context)


@login_required
@user_passes_test(is_teacher)
def devicelistEntryNew(request, room=None, date=None, std=None, entry_id=None):
    # get room id to pass in for initial data
    if room:
        room_id = get_object_or_404(Room, short_name=room).id
    else:
        room_id = None
    if request.method == "GET":
        # new empty form
        if request.user.is_staff:
            f = DevicelistEntryFormLoggedIn(initial={'room': room_id, 'datum': date, 'stunde': std})
        else:
            f = DevicelistEntryForm(initial={'room': room_id, 'datum': date, 'stunde': std})
    if request.method == "POST":
        if request.POST.get('save'):
            if request.user.is_staff:
                f = DevicelistEntryFormLoggedIn(request.POST)
            else:
                f = DevicelistEntryForm(request.POST)
            if f.is_valid():
                koffer = get_object_or_404(Room, id=int(request.POST.get('room')))
                device = Device.objects.get(id=int(request.POST.get('device')))
                if request.user.is_staff:
                    status = Status.objects.get(id=int(request.POST.get('status')))
                else:
                    status = request.POST.get('status')
                obj = f.save()
                mail_text = (
                    "ID: " + str(obj.id) + "\n" +
                    "Datum: " + request.POST.get('datum') + "\n" +
                    "Stunde: " + request.POST.get('stunde') + "\n" +
                    "Standort/Koffer: " + koffer.short_name + "\n" +
                    "Gerät: " + str(device) + "\n" +
                    "Kürzel: " + request.POST.get('krzl') + "\n" +
                    "Beschreibung: " + request.POST.get('beschreibung') + "\n" +
                    "Status: " + str(status)
                )

                if request.POST.get('email_to_second'):
                    email_to_second = request.POST.get('email_to_second')
                else:
                    email_to_second = ""

                subject = 'Neues Support Ticket ' + str(obj.id)
                thread = MailThread(subject, mail_text, email_to_second)
                thread.start()

                if room:
                    return redirect('devicelist', room=room, date=date, std=std, entry_id=entry_id)
                else:
                    return redirect('devicelist_all')
        else:
            if room:
                return redirect('devicelist', room=room, date=date, std=std, entry_id=entry_id)
            else:
                return redirect('devicelist_all')

    context = {
        'room': room,
        'devicelist': f,
        'nodelete': True,
        'date': date,
        'std': std,
        'entry_id': entry_id
    }

    return render(request, 'devicelistEntry.html', context)


@login_required
@user_passes_test(is_teacher)
def lastDeviceUsers(request, room, date, dev):
    # lte: less than equals
    devices = Booking.objects.filter(room=room, datum__lte=date).order_by('-datum', '-stunde')[:10]
    devlist = []
    for i in devices:
        # filter out current date lessons greater than current lesson
        if not (str(i.datum) == str(date) and int(i.stunde) > 1):
            # gettattr is equivalent to i.iPad_... and enables us to loop through
            devlist.append({
                'datum': i.datum,
                'stunde': i.stunde,
                'krzl': i.krzl,
                'dev': getattr(i, dev),
            })
    seit_datum = date.split("-")
    seit_datum = seit_datum[2] + "." + seit_datum[1] + "." + seit_datum[0]
    return render(request, 'deviceusers.html', {'devlist': devlist, 'dev': dev, 'seit_datum': seit_datum})


class MailThread(Thread):
    def __init__(self, subject, mail_text, email_to_second):
        super(MailThread, self).__init__()
        # Get email settings from DB
        try:
            settings = Setting.objects.filter(name='settings').first()
        except Exception as e:
            print(e)
            print("No Settings object with email configuration yet.")
        self.subject = subject
        self.mail_text = mail_text
        self.email_to = settings.email_to
        self.email_to_second = email_to_second
        self.noreply = settings.noreply_mail
        # self.backend = backend

    # run method is automatically executed on thread.start()
    def run(self):
        send_mail(
            self.subject,
            self.mail_text,
            self.noreply,
            [self.email_to, self.email_to_second],
            fail_silently=True,
        )
