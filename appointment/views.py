from django.shortcuts import render, redirect
from .models import Appointment
from .forms import AppointmentForm, AppointmentCreateForm
from django.contrib.auth.decorators import login_required, user_passes_test
# from django.contrib.admin.views.decorators import staff_member_required


def is_appointment_admin(user):
    return user.groups.filter(name='appointment_admin').exists()


@login_required
@user_passes_test(is_appointment_admin)
def create_appointment(request):
    if request.method == 'POST':
        f = AppointmentCreateForm(request.POST)
        if f.is_valid():
            f.save()
        return redirect('appointment')
    f = AppointmentCreateForm()
    return render(request, 'create_appointment.html', {'form': f, })


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
    print(appointment_items)
    return render(request, 'appointment.html', {
        'appointment_items': appointment_items,
        }
    )


def book_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == 'POST':
        f = AppointmentForm(request.POST, instance=appointment)
        if f.is_valid():
            instance = f.save(commit=False)
            instance.date = instance.date
            instance.time = instance.time
            if instance.email == instance.email_2:
                instance.save()
                return redirect('appointment')
        return render(request, 'book_appointment.html', {'form': f, 'alert': True})
    f = AppointmentForm(instance=appointment)
    return render(request, 'book_appointment.html', {'form': f})
