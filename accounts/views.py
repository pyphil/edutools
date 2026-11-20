import logging
from uuid import uuid4

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from edutools_home.models import EdutoolsSetting

from .forms import ChangeUsernameForm, RegisterUserForm
from .mail import (
    build_absolute_link,
    get_sender_address,
    normalize_email,
    post_email_ratelimit_key,
    use_https_for_links,
)
from .models import RegistrationID, UserProfile

logger = logging.getLogger(__name__)

REGISTRATION_MAIL_SUBJECT = 'Registrierung eduTools'


def _email_already_used(email):
    return (
        User.objects.filter(email__iexact=email).exists()
        or UserProfile.objects.filter(email__iexact=email, user__isnull=False).exists()
    )


def get_registration_mail_text():
    settings_obj = EdutoolsSetting.objects.filter(name='settings').first()
    return settings_obj.registration_mail_text if settings_obj else ''


def send_registration_mail(request, email):
    """Create a registration link for email and send it. Returns True on success."""
    mail_text = get_registration_mail_text()
    if '#LINK#' not in mail_text:
        logger.error(
            "Registration mail not sent: the registration mail text in the eduTools settings "
            "(EdutoolsSetting 'settings') is missing or does not contain the placeholder #LINK#."
        )
        return False
    sender = get_sender_address()
    if not sender:
        return False

    with transaction.atomic():
        # only the most recently requested link stays valid
        RegistrationID.objects.filter(user_email__iexact=email).delete()
        registration = RegistrationID.objects.create(user_email=email, uuid=uuid4().hex)

    link = build_absolute_link(request, reverse('register', args=[registration.uuid]))
    try:
        send_mail(
            REGISTRATION_MAIL_SUBJECT,
            mail_text.replace('#LINK#', link),
            sender,
            [email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send registration mail to %s", email)
        registration.delete()
        return False
    return True


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@ratelimit(key=post_email_ratelimit_key('mail'), rate='3/h', method='POST', block=True)
def email_check(request):
    email_error = False
    if request.method == 'POST':
        entered_email = normalize_email(request.POST.get('mail'))
        if '@' not in entered_email or not UserProfile.objects.filter(email__iexact=entered_email).exists():
            email_error = "not_allowed"
        elif _email_already_used(entered_email):
            email_error = "already_used"
        elif send_registration_mail(request, entered_email):
            return redirect('registration_email')
        else:
            email_error = "mail_failed"

    return render(request, 'registration/email_check.html', {'email_error': email_error})


def _get_valid_registration(uuid):
    registration = RegistrationID.objects.filter(uuid=uuid).first()
    if registration is None or registration.is_expired():
        return None
    return registration


def register(request, uuid):
    registration = _get_valid_registration(uuid)
    if registration is None:
        return render(request, 'registration/register.html', {
            'form': None,
            'user_email': None,
            'link_error': True,
            'email_error': False,
        })

    # The e-mail address is taken from the registration link only, never from the form data.
    user_email = normalize_email(registration.user_email)
    email_error = False

    if request.method == "POST":
        data = request.POST.copy()
        data['email'] = user_email
        form = RegisterUserForm(data)
        if _email_already_used(user_email):
            email_error = "already_used"
        elif not UserProfile.objects.filter(email__iexact=user_email).exists():
            email_error = "not_allowed"
        elif form.is_valid():
            with transaction.atomic():
                profile = (
                    UserProfile.objects.select_for_update()
                    .filter(email__iexact=user_email, user__isnull=True)
                    .first()
                )
                if profile is None:
                    email_error = "already_used"
                else:
                    user = form.save()
                    # put user into 'teachers' group
                    group, created = Group.objects.get_or_create(name='teachers')
                    user.groups.add(group)
                    # connect user to profile
                    profile.user = user
                    profile.save()
                    RegistrationID.objects.filter(user_email__iexact=user_email).delete()
            if not email_error:
                return redirect('account_success')
    else:
        form = RegisterUserForm(initial={'email': user_email})

    return render(request, 'registration/register.html', {
        'form': form,
        'user_email': user_email,
        'link_error': False,
        'email_error': email_error,
    })


def registration_email(request):
    return render(request, 'registration/registration_email.html', {})


def account_success(request):
    return render(request, 'registration/account_success.html', {})


class EduToolsPasswordResetView(PasswordResetView):
    """
    Password reset that uses the same sender address and link scheme as the
    registration mails.
    """

    def form_valid(self, form):
        form.save(
            use_https=use_https_for_links(self.request),
            token_generator=self.token_generator,
            from_email=get_sender_address() or None,
            email_template_name=self.email_template_name,
            subject_template_name=self.subject_template_name,
            request=self.request,
            html_email_template_name=self.html_email_template_name,
            extra_email_context=self.extra_email_context,
        )
        # skip PasswordResetView.form_valid, which would send the mail a second time
        return HttpResponseRedirect(self.get_success_url())


password_reset = ratelimit(key='ip', rate='10/m', method='POST', block=True)(
    ratelimit(key=post_email_ratelimit_key('email'), rate='3/h', method='POST', block=True)(
        EduToolsPasswordResetView.as_view()
    )
)


@login_required
def change_user(request):
    if request.GET.get('success'):
        success = True
    else:
        success = None
    form = ChangeUsernameForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        # user will be logged out automatically, so log user in again:
        login(request, request.user)
        return redirect('/accounts/change_user/?success=True')
    return render(request, 'registration/change_user.html', {'form': form, 'success': success})


def rate_limit_exceeded_view(request, exception=None):
    return render(request, 'registration/rate_limit_exceeded.html', status=429)
