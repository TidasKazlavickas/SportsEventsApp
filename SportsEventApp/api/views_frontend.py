import os
from datetime import date

from api.forms import ParticipantForm
from api.models import Event, Distance, DistanceParticipantAssociation, GroupParticipantAssociation, \
    EventParticipantAssociation
from django.conf import settings
import json
from django.shortcuts import render, get_object_or_404, redirect
from django import forms

from api.views import get_next_available_number


def event_list(request):
    events = Event.objects.all()  # Get all events from the database

    # Replace spaces with underscores and convert to lowercase for each event
    for event in events:
        event_slugified_name = event.name.replace(' ', '_').lower()

        # Construct the file path using the correct media directory
        event.logo_path = os.path.join(settings.MEDIA_URL, f"{event_slugified_name}.jpg")

    return render(request, 'frontend/event_list.html', {'events': events})

LABEL_TO_FIELD = {
    "Vardas": "first_name",
    "Pavardė": "last_name",
    "Gimimo metai": "date_of_birth",
    "Lytis": "gender",
    "El. paštas": "email",
    "Miestas": "city",
    "Klubas": "club",
    "Marškinėlių dydis": "shirt_size",
    "Telefonas": "phone_number",
    "Komentaras": "comment",
    "Sumokėjęs": "if_paid",
    "Nr. Išduotas": "if_number_received",
    "Marškiniai išduoti": "if_shirt_received",
    "Numeris": "shirt_number",
    "Distancija": "distance",
}

def participant_register(request, event_id):
    # Get the event object
    event = get_object_or_404(Event, id=event_id)

    # Get the event configuration (JSON string)
    event_config = event.required_participant_fields if event else "{}"
    config_dict = json.loads(event_config)  # Parse the JSON string

    form = ParticipantForm(request.POST or None, event=event)  # Pass the event to the form initialization

    # Dynamically hide fields based on the event's configuration
    for label, field_name in LABEL_TO_FIELD.items():
        if field_name != "distance":  # Skip the 'distance' field, we want it always visible
            if config_dict.get(label, False) is False:  # Check if the field is marked as False in the config
                if field_name in form.fields:
                    form.fields[field_name].widget = forms.HiddenInput()  # Hide the field
                    form.fields[field_name].required = False  # Optionally, make it not required

    if form.is_valid():
        participant = form.save()

        # Ensure the event-participant association is created
        if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
            EventParticipantAssociation.objects.create(event=event, participant=participant)

        # Retrieve the selected distance from POST data
        selected_distance_id = request.POST.get('distance')

        # Ensure the distance exists, and retrieve the Distance object
        selected_distance = get_object_or_404(Distance, id=selected_distance_id)

        # Create the association between participant and distance
        if not DistanceParticipantAssociation.objects.filter(distance=selected_distance, participant=participant).exists():
            DistanceParticipantAssociation.objects.create(distance=selected_distance, participant=participant)

        # Calculate the participant's age
        today = date.today()
        age = today.year - participant.date_of_birth.year - ((today.month, today.day) < (participant.date_of_birth.month, participant.date_of_birth.day))

        # Get all groups associated with the selected distance
        groups = selected_distance.groups.all()

        # Find all appropriate groups based on gender
        eligible_groups = [
            group for group in groups if group.gender.lower() == participant.gender.lower()
        ]

        # If no eligible groups found, raise an exception or handle it appropriately
        if not eligible_groups:
            return redirect('error_page')  # Or display an error message to the user

        closest_group = None
        smallest_age_diff = None

        # Loop through the eligible groups to find the closest one based on age
        for group in eligible_groups:
            age_range = json.loads(group.age)  # Assuming it's stored as a JSON string
            if age_range['age_from'] <= age <= age_range['age_to']:
                # Calculate the "closeness" of the group based on age range
                age_diff_from = age - age_range['age_from']
                age_diff_to = age_range['age_to'] - age
                smallest_age_diff_group = min(age_diff_from, age_diff_to)

                # Check if this group is closer than the previous closest
                if smallest_age_diff is None or smallest_age_diff_group < smallest_age_diff:
                    smallest_age_diff = smallest_age_diff_group
                    closest_group = group

        # If a closest group was found, create the association
        if closest_group:
            GroupParticipantAssociation.objects.create(group=closest_group, participant=participant)

        # Check if 'if_paid' is selected, and if no shirt number is entered, assign one
        if request.POST.get('if_paid') == 'on' and (not form.cleaned_data.get('shirt_number')):
            # Get the next available number from the pool (assuming you have a function to fetch the next number)
            next_available_number = get_next_available_number(selected_distance)

            # Only assign if a valid number is available
            if next_available_number is not None:
                participant.shirt_number = next_available_number
                participant.save()
    return render(request, 'frontend/add_participant.html', {'form': form, 'event': event})