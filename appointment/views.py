from django.shortcuts import render, redirect
from .models import Appointment
from .forms import AppointmentForm, AppointmentCreateForm


def appointment(request):
    appointments = Appointment.objects.all()

    dates = []
    for i in appointments:
        if i.date not in dates:
            dates.append(i.date)

    appointment_items = []
    for date in dates:
        items = Appointment.objects.filter(date=date)
        appointment_items.append((date, items))
    print(appointment_items)
    return render(request, 'appointment.html', {
        'appointment_items': appointment_items,
        }
    )


def create_appointment(request):
    if request.method == 'POST':
        f = AppointmentCreateForm(request.POST)
        if f.is_valid():
            f.save()
        return redirect('appointment')
    f = AppointmentCreateForm()
    return render(request, 'create_appointment.html', {'form': f, })


def book_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == 'POST':
        f = AppointmentForm(request.POST, instance=appointment)
        if f.is_valid():
            instance = f.save(commit=False)
            instance.date = instance.date
            instance.time = instance.time
            instance.save()
        return redirect('appointment')
    f = AppointmentForm(instance=appointment)
    return render(request, 'book_appointment.html', {'form': f})
