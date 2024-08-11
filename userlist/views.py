from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from buchungstool.models import Booking, Room
from .models import Userlist
from buchungstool_settings.models import Setting


def select(request):
    # Access only with student_access_token in production
    if not request.session.get("student_has_access"):
        try:
            settings = Setting.objects.filter(name="settings").first()
            student_access_token = settings.student_access_token
        except AttributeError:
            # development (no settings yet)
            request.session["student_has_access"] = True
        else:
            if student_access_token == "":
                # development (no access_token set in settings)
                request.session["student_has_access"] = True
            elif request.GET.get("access") != student_access_token:
                # production (no or wrong access_token)
                return render(request, "buchungstoolNoAccess.html")
            else:
                # production - correct access_token, save right to access in session
                request.session["student_has_access"] = True
                return redirect("/userlist/select/")
    elif request.GET.get("access") and request.session.get("student_has_access"):
        return redirect("/userlist/select/")

    # delete objects that are more than 20 min old
    lists = Userlist.objects.all()
    for i in lists:
        # diff = datetime.now() - i.created.replace(tzinfo=None)
        diff = timezone.now() - i.created
        if diff.total_seconds() / 60 > 20:
            i.delete()

    # only show objects made for today's date
    lists = Userlist.objects.filter(datum=datetime.now().date())

    return render(request, "userlistSelect.html", {"lists": lists})


def entry(request):
    # Access only with student_access_token in production
    if not request.session.get("student_has_access"):
        return render(
            request,
            "buchungstoolNoAccess.html",
        )

    if request.POST.get('students'):
        ipad = request.POST.get("iPad")
        pencil = request.POST.get("pencil")
        students = request.POST.get("students")

        selection_query = Userlist.objects.get(id=request.POST.get("selection"))

        save_users_query = Booking.objects.filter(
            room=selection_query.short_name,
            datum=selection_query.datum,
            stunde=selection_query.stunde,
        ).first()

        if ipad == "01":
            save_users_query.iPad_01 = students
            save_users_query.pen_01 = pencil
        if ipad == "02":
            save_users_query.iPad_02 = students
            save_users_query.pen_02 = pencil
        if ipad == "03":
            save_users_query.iPad_03 = students
            save_users_query.pen_03 = pencil
        if ipad == "04":
            save_users_query.iPad_04 = students
            save_users_query.pen_04 = pencil
        if ipad == "05":
            save_users_query.iPad_05 = students
            save_users_query.pen_05 = pencil
        if ipad == "06":
            save_users_query.iPad_06 = students
            save_users_query.pen_06 = pencil
        if ipad == "07":
            save_users_query.iPad_07 = students
            save_users_query.pen_07 = pencil
        if ipad == "08":
            save_users_query.iPad_08 = students
            save_users_query.pen_08 = pencil
        if ipad == "09":
            save_users_query.iPad_09 = students
            save_users_query.pen_09 = pencil
        if ipad == "10":
            save_users_query.iPad_10 = students
            save_users_query.pen_10 = pencil
        if ipad == "11":
            save_users_query.iPad_11 = students
            save_users_query.pen_11 = pencil
        if ipad == "12":
            save_users_query.iPad_12 = students
            save_users_query.pen_12 = pencil
        if ipad == "13":
            save_users_query.iPad_13 = students
            save_users_query.pen_13 = pencil
        if ipad == "14":
            save_users_query.iPad_14 = students
            save_users_query.pen_14 = pencil
        if ipad == "15":
            save_users_query.iPad_15 = students
            save_users_query.pen_15 = pencil
        if ipad == "16":
            save_users_query.iPad_16 = students
            save_users_query.pen_16 = pencil
        if ipad == "17":
            save_users_query.iPad_17 = students
            save_users_query.pen_17 = pencil
        if ipad == "18":
            save_users_query.iPad_18 = students
            save_users_query.pen_18 = pencil
        if ipad == "19":
            save_users_query.iPad_19 = students
            save_users_query.pen_19 = pencil
        if ipad == "20":
            save_users_query.iPad_20 = students
            save_users_query.pen_20 = pencil
        if ipad == "21":
            save_users_query.iPad_21 = students
            save_users_query.pen_21 = pencil
        if ipad == "22":
            save_users_query.iPad_22 = students
            save_users_query.pen_22 = pencil
        if ipad == "23":
            save_users_query.iPad_23 = students
            save_users_query.pen_23 = pencil
        if ipad == "24":
            save_users_query.iPad_24 = students
            save_users_query.pen_24 = pencil
        if ipad == "25":
            save_users_query.iPad_25 = students
            save_users_query.pen_25 = pencil
        if ipad == "26":
            save_users_query.iPad_26 = students
            save_users_query.pen_26 = pencil
        if ipad == "27":
            save_users_query.iPad_27 = students
            save_users_query.pen_27 = pencil
        if ipad == "28":
            save_users_query.iPad_28 = students
            save_users_query.pen_28 = pencil
        if ipad == "29":
            save_users_query.iPad_29 = students
            save_users_query.pen_29 = pencil
        if ipad == "30":
            save_users_query.iPad_30 = students
            save_users_query.pen_30 = pencil
        if ipad == "":
            error = True
        else:
            save_users_query.save()
            return redirect('userlistSuccess')

    selection_query = Userlist.objects.get(id=request.POST.get("selection"))
    selection_data = {
        "short_name": selection_query.short_name,
        "stunde": selection_query.stunde,
        "lerngruppe": selection_query.lerngruppe,
        "krzl": selection_query.krzl,
    }
    obj = Room.objects.get(short_name=selection_query.short_name)

    numbers = [""]
    for i in range(1, int(obj.device_count) + 1):
        numbers.append(("%02d" % i))

    try:
        error = error
    except Exception:
        error = False

    return render(
        request, "userlistEntry.html", {
            "numbers": numbers,
            "selection_data": selection_data,
            "selection_id": request.POST.get("selection"),
            "error": error,
        }
    )


def success(request):
    # Access only with student_access_token in production
    if not request.session.get("student_has_access"):
        return render(
            request,
            "buchungstoolNoAccess.html",
        )

    return render(request, "userlistSuccess.html", {"numbers": 0})
