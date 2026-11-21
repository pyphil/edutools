import logging
from datetime import date as date_cls, datetime, timedelta

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_ratelimit.core import is_ratelimited

from accounts.mail import get_sender_address, post_email_ratelimit_key

from .forms import AppointmentForm, AppointmentSettingForm, CreateAppointmentsForm, MailText
from .models import Appointment, AppointmentMail, AppointmentSetting

logger = logging.getLogger(__name__)

BOOKING_MAIL_SUBJECT = "Buchung Anmeldetermin"
REMINDER_MAIL_SUBJECT = "Erinnerung Anmeldetermin"

# Limits for public booking requests (POST). Can be overridden in settings.py.
BOOKING_RATELIMIT_IP = getattr(django_settings, "APPOINTMENT_RATELIMIT_IP", "10/m")
BOOKING_RATELIMIT_EMAIL = getattr(django_settings, "APPOINTMENT_RATELIMIT_EMAIL", "3/h")


def is_appointment_admin(user):
    # Only superusers and members of the dedicated group may see the booking data.
    # (is_staff alone is not enough: staff users of other eduTools apps must not
    # get access to the personal data of the children.)
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="appointment_admin").exists()


appointment_admin_required = user_passes_test(is_appointment_admin)


# ---------------------------------------------------------------- helpers

def _now():
    return timezone.localtime()


def _is_past(appointment):
    now = _now()
    return (appointment.date, appointment.time) < (now.date(), now.time().replace(tzinfo=None))


def _upcoming_free_slots():
    """Visible, unbooked slots that are not in the past."""
    now = _now()
    return (
        Appointment.objects.filter(student_name="", visible=True, date__gte=now.date())
        .exclude(date=now.date(), time__lt=now.time())
    )


def _fill_template(template, appointment):
    return (
        template
        .replace("#KIND#", appointment.student_name)
        .replace("#DATUM#", appointment.date.strftime("%d.%m.%Y"))
        .replace("#UHRZEIT#", appointment.time.strftime("%H:%M") + " Uhr")
    )


def _mail_settings():
    return AppointmentMail.objects.first()


def send_booking_mail(appointment):
    """Send the booking confirmation. Missing configuration is logged, never fatal."""
    mail_settings = _mail_settings()
    template = mail_settings.mail_text if mail_settings else ""
    if not template or not appointment.email:
        return False
    sender = get_sender_address()
    if not sender:
        return False
    try:
        EmailMessage(BOOKING_MAIL_SUBJECT, _fill_template(template, appointment), sender,
                     [appointment.email]).send()
    except Exception:
        logger.exception("Booking confirmation for appointment %s could not be sent.", appointment.pk)
        return False
    return True


def _parse_iso_date(value):
    try:
        return date_cls.fromisoformat(value[:10]) if value else None
    except (TypeError, ValueError):
        return None


def _admin_redirect(day=None):
    url = reverse("appointment_admin")
    return redirect(f"{url}?select={day.isoformat()}" if day else url)


# ---------------------------------------------------------------- public views

def appointment(request):
    settings = AppointmentSetting.objects.first()
    free_slots = _upcoming_free_slots()

    if settings and not settings.show_empty_days:
        # only dates that still have at least one free slot
        dates = free_slots.values_list("date", flat=True)
    else:
        dates = Appointment.objects.filter(date__gte=_now().date()).values_list("date", flat=True)
    dates = sorted(set(dates))

    appointment_items = [(day, free_slots.filter(date=day)) for day in dates]
    return render(
        request,
        "appointment.html",
        {
            "appointment_items": appointment_items,
            "is_admin": is_appointment_admin(request.user),
            "settings": settings,
        },
    )


def _limited_by_ip(request):
    return is_ratelimited(request, group="appointment.book.ip", key="ip",
                          rate=BOOKING_RATELIMIT_IP, method="POST", increment=True)


def _limited_by_email(request):
    # only counted for valid booking attempts, so typos in the form do not lock out a family
    return is_ratelimited(request, group="appointment.book.email", key=post_email_ratelimit_key("email"),
                          rate=BOOKING_RATELIMIT_EMAIL, method="POST", increment=True)


def book_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    is_admin = is_appointment_admin(request.user)
    settings = AppointmentSetting.objects.first()
    context = {"privacy_notice": settings.privacy_notice if settings else ""}

    def bookable():
        return appointment.visible and not appointment.is_booked and not _is_past(appointment)

    def render_public(alert=None, status=200):
        # The form is bound to the user's own input and a fresh instance that only carries
        # date/time, so data of another family who booked the slot is never shown.
        f = AppointmentForm(request.POST, instance=Appointment(date=appointment.date, time=appointment.time))
        return render(request, "book_appointment.html", {**context, "form": f, "alert": alert}, status=status)

    if request.method == "POST":
        if is_admin:
            f = AppointmentForm(request.POST, instance=appointment)
            if not f.is_valid():
                return render(request, "book_appointment.html", {**context, "form": f})
            instance = f.save()
        else:
            if not bookable():
                return render_public("booked")
            if _limited_by_ip(request):
                return render_public("limited", status=429)
            f = AppointmentForm(request.POST, instance=appointment)
            if not f.is_valid():
                return render(request, "book_appointment.html", {**context, "form": f})
            if _limited_by_email(request):
                return render_public("limited", status=429)
            # Atomic "book only if still free": the WHERE clause guarantees that two
            # simultaneous requests cannot both book (and overwrite) the same slot.
            with transaction.atomic():
                updated = Appointment.objects.filter(
                    pk=appointment.pk, student_name="", visible=True
                ).update(**f.personal_data())
            if updated != 1:
                return render_public("booked")
            instance = Appointment.objects.get(pk=appointment.pk)

        send_booking_mail(instance)
        request.session["appointment_success_id"] = instance.id
        return redirect("success_appointment")

    if is_admin or bookable():
        f = AppointmentForm(instance=appointment)
        return render(request, "book_appointment.html", {**context, "form": f})
    return redirect("appointment")


def success_appointment(request):
    id = request.session.pop("appointment_success_id", None)
    obj = Appointment.objects.filter(id=id).first() if id else None
    if obj is None:
        return redirect("appointment")
    mail_settings = _mail_settings()
    text = _fill_template(mail_settings.mail_text, obj) if mail_settings and mail_settings.mail_text else None
    return render(
        request,
        "success_appointment.html",
        {
            "text": text,
            "is_admin": is_appointment_admin(request.user),
        },
    )


# ---------------------------------------------------------------- admin views

@login_required
@appointment_admin_required
def create_appointment(request):
    if request.method == "POST":
        f = CreateAppointmentsForm(request.POST)
        if f.is_valid():
            data = f.cleaned_data
            start = datetime.combine(data["date"], data["start_time"])
            new_items = []
            for i in range(data["number"]):
                slot_time = (start + timedelta(minutes=i * data["interval"])).time()
                for _ in range(data["slots"]):
                    new_items.append(Appointment(date=data["date"], time=slot_time, visible=data["visible"]))
            Appointment.objects.bulk_create(new_items)
            return redirect("appointment")
        return render(request, "create_appointment.html", {"form": f})

    return render(request, "create_appointment.html", {})


@login_required
@appointment_admin_required
def edit_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    if request.method == "POST":
        f = AppointmentForm(request.POST, instance=appointment)
        if f.is_valid():
            instance = f.save()
            send_booking_mail(instance)
            return _admin_redirect(instance.date)
        return render(request, "book_appointment.html", {"form": f, "edit": True})

    f = AppointmentForm(instance=appointment)
    return render(request, "book_appointment.html", {"form": f, "edit": True})


@login_required
@appointment_admin_required
def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    if request.method == "POST":
        if request.POST.get("empty") or request.POST.get("empty_hide"):
            for field in Appointment.PERSONAL_FIELDS:
                setattr(appointment, field, "")
            appointment.visible = not request.POST.get("empty_hide")
            appointment.save()
        if request.POST.get("delete"):
            appointment.delete()
        return _admin_redirect(appointment.date)
    return render(request, "delete_appointment.html", {"appointment": appointment})


@login_required
@appointment_admin_required
def delete_past_appointments(request):
    """Delete all appointments (incl. personal data) before today."""
    today = _now().date()
    past = Appointment.objects.filter(date__lt=today)
    if request.method == "POST":
        count, _ = past.delete()
        messages.success(request, f"{count} vergangene Termine wurden gelöscht.")
        return _admin_redirect()
    return render(
        request,
        "delete_past_appointments.html",
        {"count": past.count(), "booked_count": past.exclude(student_name="").count(), "today": today},
    )


@login_required
@appointment_admin_required
def appointment_admin(request):
    if request.method == "POST":
        # Toggle a single appointment's visibility
        appointment_id = request.POST.get("visible_id")
        if appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.visible = not appointment.visible
            appointment.save(update_fields=["visible"])
            return _admin_redirect(appointment.date)

        # Toggle hide/unhide for the whole selected day.
        if request.POST.get("toggle_day"):
            sel_date = _parse_iso_date(request.POST.get("select"))
            if sel_date:
                hide = request.POST.get("day_hidden") == "on"
                Appointment.objects.filter(date=sel_date).update(visible=not hide)
                return _admin_redirect(sel_date)

        return _admin_redirect()

    items = Appointment.objects.all()
    all_bookings_count = items.exclude(student_name="").count()
    dates = sorted(set(items.values_list("date", flat=True)))
    current_date = _parse_iso_date(request.GET.get("select")) or (dates[0] if dates else None)
    appointments = Appointment.objects.filter(date=current_date)

    # Determine whether this day is hidden (no visible appointments)
    if current_date:
        day_hidden = not Appointment.objects.filter(date=current_date, visible=True).exists()
    else:
        day_hidden = False

    return render(
        request,
        "appointment_admin.html",
        {
            "appointments": appointments,
            "dates": dates,
            "current_date": current_date,
            "all_bookings_count": all_bookings_count,
            "day_hidden": day_hidden,
            "past_count": items.filter(date__lt=_now().date()).count(),
        },
    )


@login_required
@appointment_admin_required
def appointment_email(request):
    mail_settings = _mail_settings()

    if request.method == "POST":
        f = MailText(request.POST, instance=mail_settings)
        if f.is_valid():
            mail_settings = f.save()
            messages.success(request, "Einstellungen gespeichert")

            if request.POST.get("send_reminder"):
                sent, failed = send_reminder_mails(mail_settings.mail_text_reminder)
                if sent is None:
                    messages.error(request, "Es wurden keine Erinnerungsmails versendet: "
                                            "Erinnerungstext oder Absenderadresse fehlt.")
                elif failed:
                    messages.warning(request, f"{sent} Erinnerungsmails versendet, {failed} fehlgeschlagen.")
                else:
                    messages.success(request, f"{sent} Erinnerungsmails wurden versendet")
            return redirect("appointment_email")
    else:
        f = MailText(instance=mail_settings)

    return render(request, "appointment_email.html", {"form": f})


def send_reminder_mails(template):
    """
    Send the reminder to every booked appointment from today on.
    Returns (sent, failed), or (None, None) if the mail cannot be sent at all.
    """
    sender = get_sender_address()
    if not template or not sender:
        return None, None
    recipients = (
        Appointment.objects.filter(date__gte=_now().date())
        .exclude(student_name="").exclude(email="")
        .order_by("date", "time")
    )
    sent = failed = 0
    # one SMTP connection for all mails instead of one per mail
    with get_connection() as connection:
        for item in recipients:
            try:
                EmailMessage(REMINDER_MAIL_SUBJECT, _fill_template(template, item), sender,
                             [item.email], connection=connection).send()
                sent += 1
            except Exception:
                failed += 1
                logger.exception("Reminder for appointment %s could not be sent.", item.pk)
    return sent, failed


@login_required
@appointment_admin_required
def appointment_settings(request):
    settings = AppointmentSetting.objects.first()

    if request.method == "POST":
        f = AppointmentSettingForm(request.POST, instance=settings)
        if f.is_valid():
            f.save()
            messages.success(request, "Einstellungen gespeichert")
            return redirect("appointment_settings")
    else:
        f = AppointmentSettingForm(instance=settings)

    return render(request, "appointment_settings.html", {"form": f})
