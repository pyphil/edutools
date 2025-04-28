from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from buchungstool_settings.models import Setting
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.models import Group


def edutools_home(request):
    return render(request, 'edutools_home.html', {})


@login_required
def dsb(request):
    settings = Setting.objects.filter(name='settings').first()
    return redirect(settings.dsb_link)


@login_required
@staff_member_required
def userprofiles(request):
    userprofiles = UserProfile.objects.all()
    return render(request, "edutools_userprofiles.html", {"userprofiles": userprofiles})


@login_required
@staff_member_required
def userprofile_details(request, id):
    userprofile = UserProfile.objects.get(id=id)
    groups = Group.objects.all()
    if request.method == "POST":
        userprofile.abbr = request.POST.get("abbr")
        if userprofile.user:
            userprofile.user.groups.set(request.POST.getlist("groups"))
            user = userprofile.user
            if request.POST.get("is_staff"):
                user.is_staff = True
            else:
                user.is_staff = False
            if request.POST.get("is_active"):
                user.is_active = True
            else:
                user.is_active = False
            user.save()
        userprofile.save()
        return redirect("userprofiles")
    return render(request, "edutools_userprofile_details.html", {"userprofile": userprofile, "groups": groups})


@login_required
@staff_member_required
def userprofile_add(request):
    userprofile = UserProfile()
    groups = Group.objects.all()
    if request.method == "POST":
        userprofile.abbr = request.POST.get("abbr")
        userprofile.email = request.POST.get("email")
        if request.POST.get("user"):
            user = User.objects.get(id=request.POST.get("user"))
            userprofile.user = user
            user.groups.set(request.POST.getlist("groups"))
            if request.POST.get("is_staff"):
                user.is_staff = True
            else:
                user.is_staff = False
            if request.POST.get("is_active"):
                user.is_active = True
            else:
                user.is_active = False
            user.save()
        userprofile.save()
        return redirect("userprofiles")
    return render(request, "edutools_userprofile_details.html", {"userprofile": userprofile, "groups": groups})


# def mkr(request):
#     settings = Setting.objects.filter(name='settings').first()
#     return redirect(settings.mkr_link)
