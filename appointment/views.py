from django.shortcuts import render, redirect
from .models import Appointment, AppointmentMail
from WLANCodesWebApp.models import Config
from .forms import AppointmentForm
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from threading import Thread
from django.core.mail import send_mail
# from django.contrib.admin.views.decorators import staff_member_required


def is_appointment_admin(user):
    return user.is_staff or user.groups.filter(name='appointment_admin').exists()


@login_required
@user_passes_test(is_appointment_admin)
def create_appointment(request):
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        Appointment.objects.create(date=request.POST.get('date'), time=start_time)
        for i in range(int(request.POST.get('number')) - 1):
            hh, mm = map(int, start_time.split(':'))
            hours_added, new_mm = divmod(mm + int(request.POST.get('interval')), 60)
            new_hh = (hh + hours_added) % 24
            new_time = f"{new_hh:02d}:{new_mm:02d}"
            start_time = new_time
            Appointment.objects.create(date=request.POST.get('date'), time=new_time)

        return redirect('appointment')
    # f = AppointmentCreateForm()
    return render(request, 'create_appointment.html', {})


def appointment(request):
    appointments = Appointment.objects.all()

    # Generate a list of dates for date categories in the frontend
    dates = []
    for i in appointments:
        if i.date not in dates:
            dates.append(i.date)
    dates.sort()

    # create a list of appointments hours for the dates
    appointment_items = []
    for date in dates:
        # only append appointment if name is empty
        items = Appointment.objects.filter(date=date, student_name="")
        appointment_items.append((date, items))
    return render(request, 'appointment.html', {
        'appointment_items': appointment_items,
        'is_admin': is_appointment_admin(request.user),
        }
    )


def book_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == 'POST':
        f = AppointmentForm(request.POST, instance=appointment)
        if appointment.student_name == "":
            if f.is_valid():
                instance = f.save(commit=False)
                instance.date = instance.date
                instance.time = instance.time
                if instance.email == instance.email_2:
                    instance.save()
                    thread = mail_thread(instance)
                    thread.start()
                    # mail(instance)
                    request.session['appointment_success_id'] = instance.id
                    return redirect('success_appointment')
            return render(request, 'book_appointment.html', {'form': f, 'alert': "email"})
        else:
            return render(request, 'book_appointment.html', {'form': f, 'alert': "booked"})
    if appointment.student_name == "":
        f = AppointmentForm(instance=appointment)
        return render(request, 'book_appointment.html', {'form': f})
    else:
        return redirect('appointment')


def success_appointment(request):
    id = request.session.get('appointment_success_id')
    del request.session['appointment_success_id']
    obj = Appointment.objects.get(id=id)
    try:
        mailtextobj = AppointmentMail.objects.all().first()
        text = mailtextobj.mail_text
        text = text.replace('#KIND#', obj.student_name)
        text = text.replace('#DATUM#', obj.date.strftime('%d.%m.%Y'))
        text = text.replace('#UHRZEIT#', obj.time.strftime('%H:%M') + " Uhr")
    except AppointmentMail.DoesNotExist:
        text = None
    return render(request, 'success_appointment.html', {
        'text': text,
        'is_admin': is_appointment_admin(request.user),
        }
    )


@login_required
@user_passes_test(is_appointment_admin)
def edit_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == 'POST':
        f = AppointmentForm(request.POST, instance=appointment)

        if f.is_valid():
            instance = f.save(commit=False)
            instance.date = instance.date
            instance.time = instance.time
            if instance.email == instance.email_2:
                instance.save()
                return redirect('/appointment/appointment_admin?select=' + str(instance.date))
        return render(request, 'book_appointment.html', {'form': f, 'alert': "email"})

    f = AppointmentForm(instance=appointment)
    return render(request, 'book_appointment.html', {'form': f, 'edit': True})


@login_required
@user_passes_test(is_appointment_admin)
def delete_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == 'POST':
        if request.POST.get('empty'):
            appointment.student_name = ""
            appointment.primary_school = ""
            appointment.parents_name = ""
            appointment.email = ""
            appointment.email_2 = ""
            appointment.save()
        if request.POST.get('delete'):
            appointment.delete()
        return redirect('/appointment/appointment_admin?select=' + str(appointment.date))
    return render(request, 'delete_appointment.html', {'appointment': appointment})


@login_required
@user_passes_test(is_appointment_admin)
def appointment_admin(request):
    items = Appointment.objects.all()
    all_bookings_count = items.count() - items.filter(student_name="").count()
    dates = []
    for item in items:
        if item.date not in dates:
            dates.append(item.date)
    if dates:
        dates.sort()
    if request.GET.get('select'):
        current_date = datetime.fromisoformat(request.GET.get('select')).date()
    else:
        if dates:
            current_date = dates[0]
        else:
            current_date = None
    appointments = Appointment.objects.filter(date=current_date)

    return render(request, 'appointment_admin.html', {
        'appointments': appointments, 
        'dates': dates, 
        'current_date': current_date,
        'all_bookings_count': all_bookings_count,
        }
    )


class mail_thread(Thread):
    def __init__(self, instance):
        super(mail_thread, self).__init__()
        self.email = instance.email
        conf_noreply = Config.objects.get(name="noreply-mail")
        self.noreply = conf_noreply.setting
        try:
            obj = AppointmentMail.objects.all().first()
            self.mail_text = obj.mail_text
            self.mail_text = self.mail_text.replace('#KIND#', instance.student_name)
            self.mail_text = self.mail_text.replace('#DATUM#', instance.date.strftime('%d.%m.%Y'))
            self.mail_text = self.mail_text.replace('#UHRZEIT#', instance.time.strftime('%H:%M') + " Uhr")
        except AppointmentMail.DoesNotExist:
            self.mail_text = None
            print("no mail_text yet")

    # run method is automatically executed on thread.start()
    def run(self):
        # send mail
        if self.mail_text:
            send_mail(
                'Buchung Anmeldetermin',
                self.mail_text,
                self.noreply,
                [self.email],
                fail_silently=True,
            )


# def mail(instance):
#     conf_noreply = Config.objects.get(name="noreply-mail")
#     noreply = conf_noreply.setting
#     mail_text = f"Sie haben gebucht: {instance.date}, {instance.time}"
#     send_mail(
#         'Buchung Anmeldetermin',
#         mail_text,
#         noreply,
#         [instance.email],
#         fail_silently=True,
#     )
