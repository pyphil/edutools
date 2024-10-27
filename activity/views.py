from django.shortcuts import render, redirect
from .models import Activity, ActivityBlock, BookedActivity
from django.contrib.auth.decorators import login_required


def activity(request):
    blocks = ActivityBlock.objects.all()
    if blocks:
        current_block_id = int(request.GET.get('block', blocks.first().id))
    else:
        current_block_id = None
    alert = None
    if request.method == 'POST':
        selected_block = ActivityBlock.objects.get(id=current_block_id)
        selected_activity = Activity.objects.get(id=request.POST.get('select_activity'))
        student_name = request.POST.get('student_name').strip()
        parents_name = request.POST.get('parents_name').strip()
        count = BookedActivity.objects.filter(block=selected_block, activity=selected_activity).count()
        if count <= 5:
            booking = BookedActivity.objects.create(
                block=selected_block,
                activity=selected_activity,
                student_name=student_name,
                parents_name=parents_name
            )
            request.session['last_booking_id'] = booking.id
            return redirect('success')
        else:
            alert = selected_activity

    activities = Activity.objects.all()
    activity_list = []
    for activity in activities:
        count = BookedActivity.objects.filter(block=current_block_id, activity=activity).count()
        if count > 5:
            activity_list.append((activity.name + ' & ausgebucht').split("&"))
        else:
            activity_list.append((activity.name + '&' + str(activity.id)).split("&"))

    return render(request, 'activity.html', {
        'activities': activity_list,
        'blocks': blocks,
        'current_block_id': current_block_id,
        'alert': alert
        }
    )


def success(request):
    id = request.session.get('last_booking_id')
    obj = BookedActivity.objects.get(id=id)
    return render(request, 'success.html', {
        'activity_block': obj.block,
        'activity': obj.activity,
        }
    )


@login_required
def activity_lists(request):
    blocks = ActivityBlock.objects.all()
    if blocks:
        current_block_id = int(request.GET.get('block', blocks.first().id))
    else:
        current_block_id = None
    activities = Activity.objects.all()
    if request.GET.get('select_activity') and not request.GET.get('select_activity') == "all":
        current_activity = Activity.objects.get(id=request.GET.get('select_activity'))
        bookings = BookedActivity.objects.filter(block=current_block_id, activity=current_activity)
    else:
        current_activity = "all"
        bookings = BookedActivity.objects.filter(block=current_block_id)

    return render(request, 'activity_lists.html', {
        'blocks': blocks,
        'current_block_id': current_block_id,
        'activities': activities,
        'bookings': bookings,
        'current_activity': current_activity,
        }
    )
