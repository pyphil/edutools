from django.shortcuts import render, redirect, get_object_or_404
from .models import Activity, ActivityBlock, BookedActivity
from .forms import ActivityBlockForm, ActivityForm
from django.contrib.auth.decorators import login_required, user_passes_test


def is_activity_admin(user):
    return user.is_staff or user.groups.filter(name="activity_admin").exists()


@login_required
def activity(request):
    blocks = ActivityBlock.objects.all()
    if blocks:
        current_block_id = int(request.GET.get("block", blocks.first().id))
    else:
        current_block_id = None
    alert_full = None
    alert_exists = None
    if request.method == "POST":
        selected_block = ActivityBlock.objects.get(id=current_block_id)
        selected_activity = Activity.objects.get(id=request.POST.get("select_activity"))
        student_name = request.POST.get("student_name").strip()
        parents_name = request.POST.get("parents_name").strip()
        exists = BookedActivity.objects.filter(
            block=selected_block,
            activity=selected_activity,
            student_name=student_name,
            parents_name=parents_name,
        ).exists()

        count = BookedActivity.objects.filter(
            block=selected_block, activity=selected_activity
        ).count()
        if count <= 5 and not exists:
            alert_exists = False
            booking = BookedActivity.objects.create(
                block=selected_block,
                activity=selected_activity,
                student_name=student_name,
                parents_name=parents_name,
            )
            request.session["last_booking_id"] = booking.id
            return redirect("success")
        elif exists:
            alert_exists = True
        else:
            alert_full = selected_activity

    activities = Activity.objects.all()
    activity_list = []
    for activity in activities:
        count = BookedActivity.objects.filter(
            block=current_block_id, activity=activity
        ).count()
        if count >= 5:
            activity_list.append((activity.name + " & ausgebucht").split("&"))
        else:
            activity_list.append((activity.name + "&" + str(activity.id)).split("&"))

    return render(
        request,
        "activity.html",
        {
            "activities": activity_list,
            "blocks": blocks,
            "current_block_id": current_block_id,
            "alert_full": alert_full,
            "alert_exists": alert_exists,
        },
    )


def success(request):
    id = request.session.get("last_booking_id")
    obj = BookedActivity.objects.get(id=id)
    return render(
        request,
        "success.html",
        {
            "activity_block": obj.block,
            "activity": obj.activity,
        },
    )


@login_required
def activity_lists(request):
    blocks = ActivityBlock.objects.all()
    if blocks:
        current_block_id = int(request.GET.get("block", blocks.first().id))
    else:
        current_block_id = None
    activities = Activity.objects.all()
    if (
        request.GET.get("select_activity")
        and not request.GET.get("select_activity") == "all"
    ):
        current_activity = Activity.objects.get(id=request.GET.get("select_activity"))
        bookings = BookedActivity.objects.filter(
            block=current_block_id, activity=current_activity
        )
    else:
        current_activity = "all"
        bookings = BookedActivity.objects.filter(block=current_block_id)

    return render(
        request,
        "activity_lists.html",
        {
            "blocks": blocks,
            "current_block_id": current_block_id,
            "activities": activities,
            "bookings": bookings,
            "current_activity": current_activity,
        },
    )


def renumber_items(model):
    """Hilfsfunktion zum Neunummerieren von Items eines Models."""
    items = model.objects.all().order_by('order', 'id')
    for index, item in enumerate(items, start=1):
        if item.order != index:  # nur speichern, wenn nötig
            item.order = index
            item.save()


def update_order_on_save(instance, new_position, model):
    """Passt die Reihenfolge so an, dass das aktuelle Element an new_position steht."""
    items = list(model.objects.exclude(pk=instance.pk).order_by('order'))
    new_position = max(1, min(new_position, len(items) + 1))  # Sicherheits-Check

    # Baue neue Liste mit dem Element an der gewünschten Position
    items.insert(new_position - 1, instance)

    # Speichere neue Reihenfolge
    for index, item in enumerate(items, start=1):
        if item.order != index:
            item.order = index
            item.save()

@login_required
@user_passes_test(is_activity_admin)
def manage_blocks_and_activities(request):
    block_form = ActivityBlockForm()
    activity_form = ActivityForm()

    if request.method == "POST":
        # -------- Blocks --------
        if 'add_block' in request.POST:
            block_form = ActivityBlockForm(request.POST)
            if block_form.is_valid():
                new_block = block_form.save()
                update_order_on_save(new_block, new_block.order, ActivityBlock)
            return redirect(request.path)

        if 'save_block' in request.POST:
            block = get_object_or_404(ActivityBlock, pk=request.POST.get('block_id'))
            block.name = request.POST.get('name', block.name)
            try:
                new_position = int(request.POST.get('order', block.order))
            except ValueError:
                new_position = block.order
            block.save()  # Zuerst Name speichern
            update_order_on_save(block, new_position, ActivityBlock)
            return redirect(request.path)

        if 'delete_block' in request.POST:
            block = get_object_or_404(ActivityBlock, pk=request.POST.get('block_id'))
            block.delete()
            renumber_items(ActivityBlock)
            return redirect(request.path)

        # -------- Activities --------
        if 'add_activity' in request.POST:
            activity_form = ActivityForm(request.POST)
            if activity_form.is_valid():
                new_activity = activity_form.save()
                update_order_on_save(new_activity, new_activity.order, Activity)
            return redirect(request.path)

        if 'save_activity' in request.POST:
            activity = get_object_or_404(Activity, pk=request.POST.get('activity_id'))
            activity.name = request.POST.get('name', activity.name)
            try:
                new_position = int(request.POST.get('order', activity.order))
            except ValueError:
                new_position = activity.order
            activity.save()
            update_order_on_save(activity, new_position, Activity)
            return redirect(request.path)

        if 'delete_activity' in request.POST:
            activity = get_object_or_404(Activity, pk=request.POST.get('activity_id'))
            activity.delete()
            renumber_items(Activity)
            return redirect(request.path)

    # GET
    blocks = ActivityBlock.objects.all().order_by('order')
    activities = Activity.objects.all().order_by('order')

    context = {
        'block_form': block_form,
        'activity_form': activity_form,
        'blocks': blocks,
        'activities': activities,
    }
    return render(request, "manage_activities.html", context)

