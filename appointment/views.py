from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Appointment, AppointmentMail
from WLANCodesWebApp.models import Config
from .forms import AppointmentForm, MailText
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
# from threading import Thread
from django.core.mail import send_mail
from django.contrib import messages

# from django.contrib.admin.views.decorators import staff_member_required


def is_appointment_admin(user):
    return user.is_staff or user.groups.filter(name="appointment_admin").exists()


@login_required
@user_passes_test(is_appointment_admin)
def create_appointment(request):
    if request.method == "POST":
        start_time = request.POST.get("start_time")
        visible = request.POST.get("visible") == "on"
        for i in range(int(request.POST.get("number"))):
            hh, mm = map(int, start_time.split(":"))
            for j in range(int(request.POST.get("slots"))):
                Appointment.objects.create(date=request.POST.get("date"), time=start_time, visible=visible)
            # add interval to start_time for next appointment batch
            hours_added, new_mm = divmod(mm + int(request.POST.get("interval")), 60)
            new_hh = (hh + hours_added) % 24
            start_time = f"{new_hh:02d}:{new_mm:02d}"

        return redirect("appointment")

    return render(request, "create_appointment.html", {})


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
        # only append appointment if visible and name is empty
        items = Appointment.objects.filter(date=date, student_name="", visible=True)
        appointment_items.append((date, items))
    return render(
        request,
        "appointment.html",
        {
            "appointment_items": appointment_items,
            "is_admin": is_appointment_admin(request.user),
        },
    )


def book_appointment(request, id):
    appointment = Appointment.objects.get(id=id)

    if request.method == "POST":
        f = AppointmentForm(request.POST, instance=appointment)
        if is_appointment_admin(request.user) or (appointment.student_name == "" and appointment.visible):
            if f.is_valid():
                instance = f.save(commit=False)
                instance.date = instance.date
                instance.time = instance.time

                if instance.email == instance.email_2:
                    instance.save()

                    # --- Send confirmation email synchronously ---
                    try:
                        mail_template = AppointmentMail.objects.first().mail_text
                        if mail_template:
                            mail_text = (
                                mail_template
                                .replace("#KIND#", instance.student_name)
                                .replace("#DATUM#", instance.date.strftime("%d.%m.%Y"))
                                .replace("#UHRZEIT#", instance.time.strftime("%H:%M") + " Uhr")
                            )
                            noreply = Config.objects.get(name="noreply-mail").setting
                            send_mail(
                                "Buchung Anmeldetermin",
                                mail_text,
                                noreply,
                                [instance.email],
                                fail_silently=True,
                            )
                    except AppointmentMail.DoesNotExist:
                        # optional: log or handle missing template
                        pass

                    request.session["appointment_success_id"] = instance.id
                    return redirect("success_appointment")
            return render(request, "book_appointment.html", {"form": f, "alert": "email"})
        else:
            return render(request, "book_appointment.html", {"form": f, "alert": "booked"})

    if is_appointment_admin(request.user) or (appointment.student_name == "" and appointment.visible):
        f = AppointmentForm(instance=appointment)
        return render(request, "book_appointment.html", {"form": f})
    else:
        return redirect("appointment")


def success_appointment(request):
    id = request.session.get("appointment_success_id")
    del request.session["appointment_success_id"]
    obj = Appointment.objects.get(id=id)
    try:
        mailtextobj = AppointmentMail.objects.all().first()
        text = mailtextobj.mail_text
        text = text.replace("#KIND#", obj.student_name)
        text = text.replace("#DATUM#", obj.date.strftime("%d.%m.%Y"))
        text = text.replace("#UHRZEIT#", obj.time.strftime("%H:%M") + " Uhr")
    except AppointmentMail.DoesNotExist:
        text = None
    return render(
        request,
        "success_appointment.html",
        {
            "text": text,
            "is_admin": is_appointment_admin(request.user),
        },
    )


@login_required
@user_passes_test(is_appointment_admin)
def edit_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == "POST":
        f = AppointmentForm(request.POST, instance=appointment)

        if f.is_valid():
            instance = f.save(commit=False)
            instance.date = instance.date
            instance.time = instance.time
            if instance.email == instance.email_2:
                instance.save()

                # --- Send confirmation email synchronously ---
                try:
                    mail_template = AppointmentMail.objects.first().mail_text
                    if mail_template:
                        mail_text = (
                            mail_template
                            .replace("#KIND#", instance.student_name)
                            .replace("#DATUM#", instance.date.strftime("%d.%m.%Y"))
                            .replace("#UHRZEIT#", instance.time.strftime("%H:%M") + " Uhr")
                        )
                        noreply = Config.objects.get(name="noreply-mail").setting
                        send_mail(
                            "Buchung Anmeldetermin",
                            mail_text,
                            noreply,
                            [instance.email],
                            fail_silently=True,
                        )
                except AppointmentMail.DoesNotExist:
                    # optional: log or handle missing template
                    pass

                return redirect(
                    "/appointment/appointment_admin?select=" + str(instance.date)
                )
        return render(request, "book_appointment.html", {"form": f, "alert": "email"})

    f = AppointmentForm(instance=appointment)
    return render(request, "book_appointment.html", {"form": f, "edit": True})


@login_required
@user_passes_test(is_appointment_admin)
def delete_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.method == "POST":
        if request.POST.get("empty") or request.POST.get("empty_hide"):
            appointment.student_name = ""
            appointment.primary_school = ""
            appointment.parents_name = ""
            appointment.email = ""
            appointment.email_2 = ""
            appointment.phone = ""
            if request.POST.get("empty_hide"):
                appointment.visible = False
            else:
                appointment.visible = True
            appointment.save()
        if request.POST.get("delete"):
            appointment.delete()
        return redirect(
            "/appointment/appointment_admin?select=" + str(appointment.date)
        )
    return render(request, "delete_appointment.html", {"appointment": appointment})


@login_required
@user_passes_test(is_appointment_admin)
def appointment_admin(request):
    if request.method == "POST":
        appointment_id = request.POST.get("visible_id")
        if appointment_id:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.visible = not appointment.visible
            appointment.save()
            print(appointment.date)
        return redirect(
            reverse('appointment_admin') + "?select=" + str(appointment.date)
        )
    items = Appointment.objects.all()
    all_bookings_count = items.count() - items.filter(student_name="").count()
    dates = []
    for item in items:
        if item.date not in dates:
            dates.append(item.date)
    if dates:
        dates.sort()
    if request.GET.get("select"):
        current_date = datetime.fromisoformat(request.GET.get("select")).date()
    else:
        if dates:
            current_date = dates[0]
        else:
            current_date = None
    appointments = Appointment.objects.filter(date=current_date)

    return render(
        request,
        "appointment_admin.html",
        {
            "appointments": appointments,
            "dates": dates,
            "current_date": current_date,
            "all_bookings_count": all_bookings_count,
        },
    )


@login_required
@user_passes_test(is_appointment_admin)
def appointment_email(request):
    mail_settings = AppointmentMail.objects.first()

    if request.method == "POST":
        f = MailText(request.POST, instance=mail_settings)
        if f.is_valid():
            f.save()
            messages.success(request, "Einstellungen gespeichert")

        if request.POST.get("send_reminder"):
            appointment_objects = Appointment.objects.all()
            noreply = Config.objects.get(name="noreply-mail").setting
            mail_template = mail_settings.mail_text_reminder

            # send all reminder emails synchronously
            for appointment in appointment_objects:
                mail_text = (
                    mail_template
                    .replace("#KIND#", appointment.student_name)
                    .replace("#DATUM#", appointment.date.strftime("%d.%m.%Y"))
                    .replace("#UHRZEIT#", appointment.time.strftime("%H:%M") + " Uhr")
                )

                send_mail(
                    "Erinnerung Anmeldetermin",
                    mail_text,
                    noreply,
                    [appointment.email],
                    fail_silently=True,
                )

            messages.success(request, "Erinnerungsmails wurden versendet")
            return redirect("appointment_email")

    else:
        f = MailText(instance=mail_settings)

    return render(request, "appointment_email.html", {"form": f})
