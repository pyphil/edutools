from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from buchungstool_settings.models import Setting


def edutools_home(request):
    return render(request, 'edutools_home.html', {})


@login_required
def dsb(request):
    settings = Setting.objects.filter(name='settings').first()
    return redirect(settings.dsb_link)


# def mkr(request):
#     settings = Setting.objects.filter(name='settings').first()
#     return redirect(settings.mkr_link)
