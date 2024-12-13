import os
from datetime import date
from api.forms import ParticipantForm
from api.models import Event, Distance, DistanceParticipantAssociation, GroupParticipantAssociation, \
    EventParticipantAssociation, Participant
from django.conf import settings
import json
from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from api.views import get_next_available_number


def event_list(request):
    events = Event.objects.all()
    # Retrieve search query parameters
    search_name = request.GET.get('search_name', '')
    search_year = request.GET.get('search_year', '')

    # Apply filters
    if search_name:
        events = events.filter(name__icontains=search_name)

    if search_year:
        events = events.filter(event_date__year=search_year)

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
    event = get_object_or_404(Event, id=event_id)

    event_config = event.required_participant_fields if event else "{}"
    config_dict = json.loads(event_config)

    form = ParticipantForm(request.POST or None, event=event)

    # Dynamically hide fields based on the event's configuration
    for label, field_name in LABEL_TO_FIELD.items():
        if field_name != "distance":
            if config_dict.get(label, False) is False:
                if field_name in form.fields:
                    form.fields[field_name].widget = forms.HiddenInput()  # Hide the field
                    form.fields[field_name].required = False

    if form.is_valid():
        participant = form.save(commit=False)  # Don't save to DB yet

        # Register participant with if_paid as False
        participant.if_paid = False  # Initially set to False

        participant.save()  # Save the participant now

        # Create Event-Participant Association
        if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
            EventParticipantAssociation.objects.create(event=event, participant=participant)

        # Process selected distance
        selected_distance_id = request.POST.get('distance')
        selected_distance = get_object_or_404(Distance, id=selected_distance_id)

        if not DistanceParticipantAssociation.objects.filter(distance=selected_distance, participant=participant).exists():
            DistanceParticipantAssociation.objects.create(distance=selected_distance, participant=participant)

        # Calculate the participant's age
        today = date.today()
        age = today.year - participant.date_of_birth.year - ((today.month, today.day) < (participant.date_of_birth.month, participant.date_of_birth.day))

        # Find eligible groups based on gender and age
        groups = selected_distance.groups.all()
        eligible_groups = [group for group in groups if group.gender.lower() == participant.gender.lower()]

        closest_group = None
        smallest_age_diff = None

        for group in eligible_groups:
            age_range = json.loads(group.age)
            if age_range['age_from'] <= age <= age_range['age_to']:
                # Calculate closeness of age to the group
                age_diff_from = age - age_range['age_from']
                age_diff_to = age_range['age_to'] - age
                smallest_age_diff_group = min(age_diff_from, age_diff_to)

                if smallest_age_diff is None or smallest_age_diff_group < smallest_age_diff:
                    smallest_age_diff = smallest_age_diff_group
                    closest_group = group

        if closest_group:
            GroupParticipantAssociation.objects.create(group=closest_group, participant=participant)

        # Redirect to the payment options page or simulate payment if necessary
        return redirect('payment_options', participant_id=participant.id, event_id=event.id, selected_distance=selected_distance.id)

    return render(request, 'frontend/add_participant.html', {'form': form, 'event': event})


def participant_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = Participant.objects.filter(events__id=event_id)

    distances = Distance.objects.filter(eventdistanceassociation__event=event)

    # Filter by search query parameters
    search_first_name = request.GET.get('search_first_name', '')
    search_last_name = request.GET.get('search_last_name', '')
    search_number = request.GET.get('search_number', '')
    search_club = request.GET.get('search_club', '')
    search_distance = request.GET.get('search_distance', '')

    # Apply filters
    if search_first_name:
        participants = participants.filter(first_name__icontains=search_first_name)

    if search_last_name:
        participants = participants.filter(last_name__icontains=search_last_name)

    if search_number:
        participants = participants.filter(id=search_number)

    if search_club:
        participants = participants.filter(club__icontains=search_club)

    if search_distance:
        participants = participants.filter(distances__id=search_distance)

    for participant in participants:
        participant.distance = participant.distances.first()

    return render(request, 'frontend/participant_list.html', {
        'event': event,
        'participants': participants,
        'distances': distances
    })

def event_photos(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Define the path where the event's photos are stored
    event_folder = os.path.join(settings.MEDIA_ROOT, 'event_photos', event.name)

    if os.path.exists(event_folder):
        photo_files = [f for f in os.listdir(event_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    else:
        photo_files = []

    # Construct the URLs for the photos
    photo_urls = [os.path.join(settings.MEDIA_URL, 'event_photos', event.name, photo) for photo in photo_files]

    return render(request, 'frontend/event_photos.html', {'event': event, 'photo_urls': photo_urls})

def show_results(request, event_id):
    # Fetch the event using event_id
    event = get_object_or_404(Event, id=event_id)
    result_link = event.result_link
    return render(request, 'frontend/show_results.html', {'result_link': result_link})

def payment_options(request, participant_id, event_id, selected_distance):
    participant = get_object_or_404(Participant, id=participant_id)
    event = get_object_or_404(Event, id=event_id)
    selected_distance = get_object_or_404(Distance, id=selected_distance)

    if participant.if_paid:
        return redirect('participant_details', participant_id=participant_id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if payment_method == 'online_payment':  # Simulate online payment
            participant.if_paid = True
            participant.save()

            if not participant.shirt_number:
                next_available_number = get_next_available_number(selected_distance)
                if next_available_number:
                    participant.shirt_number = next_available_number
                    participant.save()

            return redirect('payment_success', participant_id=participant_id)

        elif payment_method == 'cash_payment':
            return redirect('event_detail', event_id=event_id)

    return render(request, 'frontend/payment_options.html', {'participant': participant, 'event': event})

def payment_success(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    return render(request, 'frontend/payment_success.html', {'participant': participant})

def payment_pending(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    return render(request, 'frontend/payment_pending.html', {'participant': participant})
