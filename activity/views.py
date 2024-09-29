from django.shortcuts import render, redirect
from .models import Activity, ActivityBlock, BookedActivity


def activity(request):
    blocks = ActivityBlock.objects.all()
    current_block_id = int(request.GET.get('block', blocks.first().id))
    alert = None
    if request.method == 'POST':
        selected_block = ActivityBlock.objects.get(id=current_block_id)
        selected_activity = Activity.objects.get(name=request.POST.get('select_activity'))
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
            activity_list.append(activity.name + ' - ausgebucht')
        else:
            activity_list.append(activity.name)

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
