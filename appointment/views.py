from django.shortcuts import render
from .models import Appointment


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
