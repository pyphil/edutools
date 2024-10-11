from django.shortcuts import redirect, render, get_object_or_404
from .models import Booking, Room, Category, FAQ
from .forms import BookingFormIpad, RoomAlertForm, FAQForm
from userlist.models import Userlist
from buchungstool_settings.models import Setting
from devicelist.models import Device, Status
from django.contrib.auth.decorators import login_required, user_passes_test
import datetime
from django.utils import timezone
from uuid import uuid4


def is_teacher(user):
    return user.is_staff or user.groups.filter(name='teachers').exists()


@login_required
@user_passes_test(is_teacher)
def rooms(request):
    rooms = Room.objects.all()

    try:
        info_frontpage = Setting.objects.get(name="settings")
        info_frontpage = info_frontpage.info_frontpage
        if info_frontpage == "":
            info_frontpage = False
    except Setting.DoesNotExist:
        info_frontpage = False
        # call first run function
        first_run()

    categories = Category.objects.all()

    return render(
        request, 'buchungstoolRooms.html',
        {'rooms': rooms, 'info_frontpage': info_frontpage, 'categories': categories}
    )


@login_required
@user_passes_test(is_teacher)
def home(request, room=None):
    if room:
        room_obj = get_object_or_404(Room, short_name=room)

    if room is None:
        return redirect('/')

    if request.POST.get('alert_save'):
        alert_form = RoomAlertForm(request.POST, instance=room_obj)
        if alert_form.is_valid():
            alert_form.save()
    else:
        alert_form = RoomAlertForm(instance=room_obj)

    direction = None
    if request.GET.get('direction'):
        direction = request.GET.get('direction')
    dates, offset, currentdate = getWeekCalendar(request, direction)
    currentdate = currentdate.strftime('%Y-%m-%d')

    checked = False
    stunden = 7
    if request.GET.get('checked') == 'True':
        # if hidden input value is True: switch is turned off
        request.session['switch'] = 'off'

    if request.GET.get('switch') == 'on' or request.session.get('switch') == 'on':
        request.session['switch'] = 'on'
        checked = True
        stunden = 11
    range_stunden = range(1, stunden+1)
    btncontent = []
    for std in range_stunden:
        for date in dates:
            dbobject = Booking.objects.filter(
                room=room,
                datum=date['isodate'],
                stunde=std
            ).first()
            if dbobject:
                btncontent.append(
                    {
                        'id': dbobject.id,
                        'lerngruppe': dbobject.lerngruppe,
                        'date': date,
                        'std': std,
                        'krzl': dbobject.krzl,
                        'series': dbobject.series_id,
                    }
                )
            else:
                btncontent.append(["frei", date, std])
                btncontent.append(
                    {'id': 0, 'lerngruppe': "frei", 'date': date, 'std': std})

    response = render(
        request, 'buchungstoolHome.html',
        {
            'room': room_obj.short_name,
            'room_text': room_obj.room + " - " + room_obj.description,
            'room_alert': room_obj.alert,
            'dates': dates,
            'btncontent': btncontent,
            'currentdate': currentdate,
            'range_stunden': range_stunden,
            'checked': checked,
            'alert_form': alert_form,
        }
    )
    response.set_cookie('offset', offset)
    return response


@login_required
@user_passes_test(is_teacher)
def eintrag(request, accordion=None, room=None, id=None):
    # if not request.session.get('has_access'):
    #     return render(request, 'buchungstoolNoAccess.html',)

    if accordion or request.GET.get('accordion'):
        accordion = "open"
    else:
        accordion = "closed"

    if request.POST.get('reload'):
        return redirect('/booking/buchungstool/' + room + "/" + str(id) + '/?accordion="open"#userlist')

    room_obj = Room.objects.get(short_name=room)

    if id != 0:
        entry_obj = get_object_or_404(Booking, id=id)
        isodate = str(entry_obj.datum)
        date = entry_obj.datum.strftime('%d.%m.%Y')
        lerngruppe = entry_obj.lerngruppe
        std = entry_obj.stunde
        krzl = entry_obj.krzl
        series_id = entry_obj.series_id

        state, userlist = getUserlist(room, isodate, std)
        initial_list = []
        for i in userlist:
            initial_list.append(i.value())
        if request.method == 'GET':
            request.session['initial_list'] = initial_list
    elif id == 0:
        # neuer Eintrag Variablen vorbereiten
        isodate = request.GET.get('isodate')
        date = datetime.datetime.strptime(isodate, '%Y-%m-%d').strftime('%d.%m.%Y')
        std = request.GET.get('std')
        lerngruppe = ""
        krzl = ""
        state = None
        userlist = None
        series_id = None

    if request.POST.get('submit_student'):
        f = BookingFormIpad(request.POST, instance=entry_obj)

        z = 0
        changed_fields = []
        for i in f:
            if i.value() != request.session.get('initial_list')[z]:
                changed_fields.append(i.name)
            z += 1
        del request.session['initial_list']
        if f.is_valid():
            obj = f.save(commit=False)
            obj.save(update_fields=changed_fields)
            return redirect('/booking/buchungstool/' + room + "/" + str(id) + '/?accordion="open"#userlist')
        errors = f.errors

    if request.POST.get('freischalten'):
        state = "off"
        if request.POST.get('freischalten') == "on":
            # the created variable is True if a new object was created by get_or_create
            # However, it's not needed here
            entry, created = Userlist.objects.get_or_create(
                short_name=room,
                datum=isodate,
                stunde=std,
                lerngruppe=lerngruppe,
                krzl=krzl,
            )
            # entry.created = datetime.datetime.now()
            entry.created = timezone.now()
            entry.save()
            state = "on"
            return redirect('/booking/buchungstool/' + room + "/" + str(id) + '/?accordion="open"#userlist')
        elif request.POST.get('freischalten') == "off":
            delete_objects = Userlist.objects.filter(
                short_name=room,
                datum=isodate,
                stunde=std,
            )
            for obj in delete_objects:
                obj.delete()
            return redirect('/booking/buchungstool/' + room + "/" + str(id) + '/?accordion="open"#0')

    warning = False
    alert = False
    blocked_dates = None

    if request.POST.get('save'):
        selected_date = request.POST.get('selection')
        # Prüfen ob Felder leer sind
        if request.POST.get('lerngruppe') == "" or request.POST.get('krzl') == "" or request.POST.get('lerngruppe') == " " or request.POST.get('krzl') == " ":
            warning = True
        else:
            if selected_date == '0':
                # Neue Buchung für einen Termin
                new = Booking.objects.get_or_create(
                    room=room,
                    lerngruppe=request.POST.get('lerngruppe'),
                    datum=isodate,
                    stunde=std,
                    krzl=request.POST.get('krzl').upper()[:15]
                )
                return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)
            if selected_date != '0':
                selected_series = getDateSeries(isodate, int(selected_date))
                # Serie auf besetzte Termine testen
                # Booking.objects.filter(datum="2022-02-23").filter(stunde='6').exists()
                # .datum.isoformat().split('-')
                blocked_dates = []
                for i in selected_series:
                    d = i['date'].split('.')
                    d = d[2] + "-" + d[1] + "-" + d[0]
                    if Booking.objects.filter(room=room).filter(datum=d).filter(stunde=std).exists():
                        blocked_dates.append(d)

                # wenn alle frei: einen oder alle buchen
                if blocked_dates == []:
                    series_id = uuid4().hex
                    for i in selected_series:
                        d = i['date'].split('.')
                        d = d[2] + "-" + d[1] + "-" + d[0]
                        new = Booking(
                            room=room,
                            lerngruppe=request.POST.get('lerngruppe'),
                            datum=d,
                            stunde=std,
                            series_id=series_id,
                            krzl=request.POST.get('krzl').upper()[:15]
                        )
                        new.save()
                    return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)
                # sonst: render entry mit alert in template
                else:
                    alert = True

    update = False

    if request.POST.get('update'):
        if request.POST.get('lerngruppe') == "" or request.POST.get('krzl') == "" or request.POST.get('lerngruppe') == " " or request.POST.get('krzl') == " ":
            warning = True
            update = True
        else:
            entry_obj.lerngruppe = request.POST.get('lerngruppe')
            entry_obj.krzl = request.POST.get('krzl').upper()[:15]
            entry_obj.save()
            return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)

    if request.POST.get('update_all'):
        if request.POST.get('lerngruppe') == "" or request.POST.get('krzl') == "" or request.POST.get('lerngruppe') == " " or request.POST.get('krzl') == " ":
            warning = True
            update = True
        else:
            all_obj = Booking.objects.filter(series_id=entry_obj.series_id)
            for i in all_obj:
                i.lerngruppe = request.POST.get('lerngruppe')
                i.krzl = request.POST.get('krzl').upper()[:15]
                i.save()
            return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)

    if request.POST.get('cancel'):
        # redirect to home
        return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)

    if request.POST.get('delete'):
        context = {
            'date': isodate,
            'lerngruppe': lerngruppe,
            'std': std,
            'room': room,
            'buttondate': date,
            'krzl': krzl,
            'id': id,
        }
        return render(request, 'buchungstoolConfirmation.html', context)

    if request.POST.get('delete_future'):
        future_obj = Booking.objects.filter(series_id=entry_obj.series_id, datum__gte=entry_obj.datum)
        series = [i.datum for i in future_obj]
        series = ', '.join(map(str, series))
        context = {
            'date': isodate,
            'lerngruppe': lerngruppe,
            'std': std,
            'room': room,
            'buttondate': date,
            'krzl': krzl,
            'id': id,
            'series_id': series_id,
            'series': series,
        }
        return render(request, 'buchungstoolConfirmation.html', context)

    if request.POST.get('deleteconfirmed'):
        entry_obj.delete()
        delete_userlist_entry = Userlist.objects.filter(
            short_name=room,
            datum=isodate,
            stunde=std,
        ).first()
        if delete_userlist_entry:
            delete_userlist_entry.delete()
        return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)

    if request.POST.get('deleteconfirmed_future'):
        future_obj = Booking.objects.filter(series_id=entry_obj.series_id, datum__gte=entry_obj.datum)
        for i in future_obj:
            delete_userlist_entry = Userlist.objects.filter(
                short_name=i.room,
                datum=i.datum,
                stunde=i.stunde,
            ).first()
            if delete_userlist_entry:
                delete_userlist_entry.delete()
            i.delete()
        return redirect('/booking/buchungstool/' + room + '/?date=' + isodate)

    date_series = getDateSeries(isodate)

    if blocked_dates:
        blocked_dates = ', '.join(blocked_dates)
    else:
        blocked_dates = None
    if room_obj.device_count:
        device_count = int(room_obj.device_count)
    else:
        device_count = None
    try:
        errors = errors
    except Exception:
        errors = None

    return render(
        request, 'buchungstoolEntry.html',
        {
            'room': room,
            'device_count': device_count,
            'room_text': room_obj.room + " - " + room_obj.description,
            'isodate': isodate,
            'date': date,
            'buttontext': lerngruppe,
            'std': std,
            'krzl': krzl,
            'date_series': date_series,
            'userlist': userlist,
            'state': state,
            'accordion': accordion,
            'warning_empty': warning,
            'update': update,
            'alert': alert,
            'blocked_dates': blocked_dates,
            'entry_id': id,
            'series_id': series_id,
            'errors': errors,
        }
    )


def getWeekCalendar(request, direction=None):
    try:
        offset = int(request.COOKIES['offset'])
    except Exception:
        pass

    if request.GET.get('currentdate'):
        currentdate = request.GET.get('currentdate')
        currentdate = datetime.datetime.strptime(currentdate, '%Y-%m-%d')
        currentdate = currentdate.date()
        offset = 0
    elif request.GET.get('currentdate_nav'):
        currentdate = request.GET.get('currentdate_nav')
        currentdate = datetime.datetime.strptime(currentdate, '%Y-%m-%d')
        currentdate = currentdate.date()
    elif request.GET.get('date'):
        offset = 0
        currentdate = request.GET.get('date')
        currentdate = datetime.datetime.strptime(currentdate, '%Y-%m-%d')
        currentdate = currentdate.date()
    else:
        currentdate = datetime.date.today()
        offset = 0

    # Starts with knowing the day of the week
    # .weekday statt [2] funktioniert erst ab Python 3.9
    week_day = currentdate.isocalendar()[2]

    if direction == "forward":
        offset = offset + 7
    if direction == "back":
        offset = offset - 7

    # Calculates Starting date for this case by subtracting current date with
    # time delta of the day of the week
    start_date = currentdate - datetime.timedelta(days=week_day)
    start_date = start_date + datetime.timedelta(days=offset)

    # Prints the list of dates in a current week
    # weekdays = ["Mo, ", "Di, ", "Mi, ", "Do, ", "Fr, ", "Sa, ", "So, "]
    weekdays = ["Mo, ", "Di, ", "Mi, ", "Do, ", "Fr, "]
    dates = []
    i = 1
    for day in weekdays:
        isodate = (start_date + datetime.timedelta(days=i)).isoformat()

        dates.append(
            {"weekday": day, "date": datetime.datetime.strptime(
                isodate, '%Y-%m-%d').strftime('%d.%m.%Y'),
                "isodate": str(isodate)
             }
        )
        i += 1

    return dates, offset, currentdate


def getDateSeries(date, end=None):
    if end is None:
        end = 24

    date = datetime.datetime.strptime(date, '%Y-%m-%d')

    date_series = []
    date_series.append({'date': date.strftime('%d.%m.%Y'), 'item': 0})
    for i in range(end):
        date = date + datetime.timedelta(days=7)
        date_series.append(
            {'date': date.strftime('%d.%m.%Y'), 'item': i + 1}
        )

    return date_series


def getUserlist(room, isodate, std):
    # userlist = []

    dbobject = Booking.objects.get(
        room=room,
        datum=isodate,
        stunde=std
    )

    f = BookingFormIpad(instance=dbobject)

    # delete objects that are more than 20 min old
    lists = Userlist.objects.all()
    for i in lists:
        # diff = datetime.datetime.now() - i.created.replace(tzinfo=None)
        diff = timezone.now() - i.created
        if diff.total_seconds()/60 > 20:
            i.delete()

    activated = Userlist.objects.filter(
        short_name=dbobject.room,
        datum=isodate,
        stunde=std
    ).exists()

    if activated:
        return "on", f
    else:
        return "off", f


@login_required
@user_passes_test(is_teacher)
def userlistInfo(request):
    return render(request, 'buchungstoolUserlistInfo.html', {})


@login_required
@user_passes_test(is_teacher)
def faq(request):
    if request.method == 'POST':
        if request.POST.get('save'):
            f = FAQForm(request.POST)
            if f.is_valid():
                f.save()
                return redirect('faq')
        if request.POST.get('edit_save'):
            obj = FAQ.objects.get(id=int(request.POST.get('edit_save')))
            form = FAQForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                return redirect('/booking/buchungstool/faq/?open=' + str(obj.id) + '#heading_' + str(obj.id))
    else:
        # new faq item
        new_faq = FAQForm()
        # create a list forms for displaying and editing faqs
        objects = FAQ.objects.all()
        forms = [FAQForm(instance=obj) for obj in objects]
        if request.GET.get('open'):
            open = int(request.GET.get('open'))
        else:
            open = None
        return render(request, 'buchungstoolFAQ.html', {'forms': forms, 'new_faq': new_faq, 'open': open})


def first_run():
    # create iPad devices
    for i in range(1, 17):
        devices, created = Device.objects.get_or_create(dbname='iPad_' + "{:02d}".format(i))
        if created:
            devices.dbname = 'iPad_' + '{:02d}'.format(i)
            devices.device = 'iPad ' + '{:02d}'.format(i)
            devices.position = i
            devices.save()

    # create pens
        for i in range(1, 17):
            devices, created = Device.objects.get_or_create(dbname='pen_' + '{:02d}'.format(i))
            if created:
                devices.dbname = 'pen_' + '{:02d}'.format(i)
                devices.device = 'Stift ' + '{:02d}'.format(i)
                devices.position = i
                devices.save()

    # create status
    status_texts = [
        ('offen', 'text-danger'),
        ('in Bearbeitung', 'text-warning'),
        ('gelöst', 'text-success'),
        ('irreparabel', 'text-danger'),
    ]

    for s in status_texts:
        devices, created = Status.objects.get_or_create(status=s[0])
        if created:
            devices.status = s[0]
            devices.color = s[1]
            devices.save()
