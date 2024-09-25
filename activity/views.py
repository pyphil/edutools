from django.shortcuts import render
from .models import Activity
from .forms import ActivityForm


def activity(request):
    f = ActivityForm()
    return render(request, 'activity.html', {'form': f})
