import os

from django.shortcuts import render

from api.models import Event
from django.conf import settings


def event_list(request):
    events = Event.objects.all()  # Get all events from the database

    # Replace spaces with underscores and convert to lowercase for each event
    for event in events:
        event_slugified_name = event.name.replace(' ', '_').lower()

        # Construct the file path using the correct media directory
        event.logo_path = os.path.join(settings.MEDIA_URL, f"{event_slugified_name}.jpg")

    return render(request, 'frontend/event_list.html', {'events': events})
