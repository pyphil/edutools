from django.shortcuts import render, redirect
from .models import Appointment
from .forms import AppointmentForm
from django.contrib.auth.decorators import login_required, user_passes_test
# from django.contrib.admin.views.decorators import staff_member_required


def is_appointment_admin(user):
    return user.groups.filter(name='appointment_admin').exists()


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

    # create a list of appointments hours for the dates
    appointment_items = []
    for date in dates:
        # only append appointment if name is empty
        items = Appointment.objects.filter(date=date, student_name="")
        appointment_items.append((date, items))
    return render(request, 'appointment.html', {
        'appointment_items': appointment_items,
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
                    return redirect('appointment')
            return render(request, 'book_appointment.html', {'form': f, 'alert': "email"})
        else:
            return render(request, 'book_appointment.html', {'form': f, 'alert': "booked"})
    if appointment.student_name == "":
        f = AppointmentForm(instance=appointment)
        return render(request, 'book_appointment.html', {'form': f})
    else:
        return redirect('appointment')


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
                return redirect('appointment_admin')
        return render(request, 'book_appointment.html', {'form': f, 'alert': "email"})

    f = AppointmentForm(instance=appointment)
    return render(request, 'book_appointment.html', {'form': f})


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
        return redirect('appointment_admin')
    return render(request, 'delete_appointment.html', {'appointment': appointment})


@login_required
@user_passes_test(is_appointment_admin)
def appointment_admin(request):
    # appointments = Appointment.objects.all()
    appointments = Appointment.objects.all()
    return render(request, 'appointment_admin.html', {'appointments': appointments})
