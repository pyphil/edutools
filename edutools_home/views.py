from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from buchungstool_settings.models import Setting
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
import csv
from django.contrib import messages


def edutools_home(request):
    return render(request, "edutools_home.html", {})


@login_required
def dsb(request):
    settings = Setting.objects.filter(name="settings").first()
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
        userprofile.abbr = request.POST.get("abbr").upper()
        userprofile.email = request.POST.get("email").casefold()
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
    return render(
        request,
        "edutools_userprofile_details.html",
        {"userprofile": userprofile, "groups": groups},
    )


@login_required
@staff_member_required
def userprofile_add(request):
    userprofile = UserProfile()
    groups = Group.objects.all()
    if request.method == "POST":
        userprofile.abbr = request.POST.get("abbr").upper()
        userprofile.email = request.POST.get("email").casefold()
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
    return render(
        request,
        "edutools_userprofile_details.html",
        {"userprofile": userprofile, "groups": groups},
    )


@login_required
@staff_member_required
def import_userprofiles_from_csv(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("import_userprofiles")

        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                abbr = row.get("Krzl")
                email = row.get("email")
                if abbr and email:
                    userprofile, created = UserProfile.objects.get_or_create(
                        email=email
                    )
                    userprofile.abbr = abbr
                    userprofile.save()
                else:
                    messages.error(
                        request,
                        f"An error occurred: Make sure there are 'Krzl' and 'email' columns.",
                    )
                    return redirect("import_userprofiles")
            messages.success(request, "UserProfiles imported successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("import_userprofiles")
        return redirect("userprofiles")

    return render(request, "edutools_import_userprofiles.html")


# def mkr(request):
#     settings = Setting.objects.filter(name='settings').first()
#     return redirect(settings.mkr_link)
