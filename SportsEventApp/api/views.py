from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm, GroupForm, DistanceForm, ParticipantRegistrationForm, ParticipantForm
from .models import Group, Event, Distance, EventDistanceAssociation, Participant, EventParticipantAssociation
import json

def event_list(request):
    events = Event.objects.all()  # Fetch all events
    return render(request, 'api/event_list.html', {'events': events})

def create_event(request):
    if request.method == 'POST':
        event_form = EventForm(request.POST)
        group_form = GroupForm(request.POST)
        distance_form = DistanceForm(request.POST)

        if 'submit_event' in request.POST and event_form.is_valid():

            # Extract the cleaned data
            event_name = event_form.cleaned_data['event_name']
            required_participant_fields = event_form.cleaned_data['required_participant_fields']
            reglament_lt = event_form.cleaned_data['reglament_lt']
            reglament_en = event_form.cleaned_data['reglament_en']
            registration_deadline = event_form.cleaned_data['registration_deadline']
            payment_project_id = event_form.cleaned_data['payment_project_id']
            payment_password = event_form.cleaned_data['payment_password']
            event_result_link = event_form.cleaned_data['event_result_link']

            fields = {
                'Vardas': event_form.cleaned_data.get('is_name_required', False),
                'Pavardė': event_form.cleaned_data.get('is_surname_required', False),
                'Gimimo metai': event_form.cleaned_data.get('is_birth_year_required', False),
                'Lytis': event_form.cleaned_data.get('is_gender_required', False),
                'El. paštas': event_form.cleaned_data.get('is_email_required', False),
                'Miestas': event_form.cleaned_data.get('is_city_required', False),
                'Klubas': event_form.cleaned_data.get('is_club_required', False),
                'Marškinėlių dydis': event_form.cleaned_data.get('is_shirt_size_required', False),
                'Telefonas': event_form.cleaned_data.get('is_phone_required', False),
                'Sportident': event_form.cleaned_data.get('is_sportident_required', False),
            }

            # Creating a string that looks like JSON, but is a plain string
            # Example: '{"Vardas": true, "Pavardė": false, "Gimimo metai": true}'
            fields_str = '{' + ', '.join(f'"{key}": {str(value).lower()}' for key, value in fields.items()) + '}'
            # Create a new Event instance and save to the database
            event = Event(
                name=event_name,
                required_participant_fields=fields_str,  # Save as a string resembling JSON
                reglament_lt=reglament_lt,
                reglament_en=reglament_en,
                registration_deadline=registration_deadline,
                payment_project_id=payment_project_id,
                payment_password=payment_password,
                event_result_link=event_result_link,
            )
            event.save()
            return redirect('create_event')  # Redirect to refresh the page
        elif 'submit_group' in request.POST and group_form.is_valid():
            # Combine age_from and age_to into a dictionary and convert to JSON string
            age_data = json.dumps({
                'age_from': group_form.cleaned_data['age_from'],
                'age_to': group_form.cleaned_data['age_to']
            })
            # Determine gender based on the form's boolean fields
            if group_form.cleaned_data['male']:  # This will be True if checked
                gender_data = "male"
            elif group_form.cleaned_data['female']:  # This will be True if checked
                gender_data = "female"
            else:
                gender_data = None  # If neither is selected, set to None or handle accordingly

            # Save the group data to the database
            participant_group = Group(
                name=group_form.cleaned_data['name'],
                age=age_data,  # Save as JSON string
                gender=gender_data,
            )
            participant_group.save()
            return redirect('create_event')  # Redirect to refresh the page
        elif 'submit_distance' in request.POST and distance_form.is_valid():
            # Serialize data to JSON
            numbers_data = json.dumps({
                'numbers_from': distance_form.cleaned_data['numbers_from'],
                'numbers_to': distance_form.cleaned_data['numbers_to']
            })
            special_numbers_data = json.dumps({
                'special_numbers_from': distance_form.cleaned_data['extra_numbers_from'],
                'special_numbers_to': distance_form.cleaned_data['extra_numbers_to']
            })
            participant_count = None if not distance_form.cleaned_data['if_race'] else distance_form.cleaned_data['race_participant_count']

            # Create and save the Distance object
            distance = Distance(
                name_lt=distance_form.cleaned_data['name_lt'],
                name_en=distance_form.cleaned_data['name_en'],
                numbers=numbers_data,
                special_numbers=special_numbers_data,
                price=distance_form.cleaned_data['price'],
                price_extra=distance_form.cleaned_data['extra_price'],
                price_extra_date=distance_form.cleaned_data['extra_price_date'],
                if_race=distance_form.cleaned_data['if_race'],
                race_participant_count=participant_count
            )
            distance.save()

            # Create and save the association with the selected event
            selected_event = distance_form.cleaned_data['event']
            association = EventDistanceAssociation(event=selected_event, distance=distance)
            association.save()

            return redirect('create_event')  # Redirect to refresh the page
    else:
        event_form = EventForm()
        group_form = GroupForm()
        distance_form = DistanceForm()

    # Fetch existing groups for display
    groups = Group.objects.all()
    # Parse the 'age' field into 'age_from' and 'age_to' for each group
    for group in groups:
        if group.age:  # Check if the age field contains data
            try:
                age_data = json.loads(group.age)  # Parse the JSON data
                group.age_from = age_data.get('age_from', None)
                group.age_to = age_data.get('age_to', None)
            except json.JSONDecodeError:
                group.age_from = None
                group.age_to = None

    return render(request, 'api/create_event.html', {'event_form': event_form, 'group_form': group_form, 'distance_form':distance_form, 'groups': groups})


def register_participant(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)  # Pass POST data into the form
        if form.is_valid():  # Ensure the form is valid
            participant = form.save()
            return redirect('register_participant')  # Redirect to the same page to clear the form
        else:
            # If form is not valid, show errors
            print(form.errors)
    else:
        form = ParticipantForm()  # Create an empty form instance for GET request

    return render(request, 'api/register_participant.html', {'form': form})

def update_distances(request):
    event_id = request.GET.get('event_id')
    distances = EventDistanceAssociation.objects.filter(event_id=event_id)
    distance_list = [{'id': d.distance.id, 'name_lt': d.distance.name_lt} for d in distances]
    return JsonResponse({'distances': distance_list})

def participant_list(request):
    participants = Participant.objects.all()  # Get all participants
    return render(request, 'api/participant_list.html', {'participants': participants})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = Participant.objects.filter(event_participations__event=event)

    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
                EventParticipantAssociation.objects.create(event=event, participant=participant)
            return redirect('event_detail', event_id=event_id)
    else:
        form = ParticipantForm()

    return render(request, 'api/event_detail.html', {'event': event, 'form': form, 'participants': participants})

import json
from django.shortcuts import render, get_object_or_404, redirect
from .models import Event

def edit_event(request, event_id):
    # Retrieve the existing event or return 404 if not found
    event = get_object_or_404(Event, id=event_id)
    required_fields = json.loads(event.required_participant_fields)

    if request.method == 'POST':
        # Extract data from the POST request
        name = request.POST.get('name')
        selected_fields = request.POST.getlist('required_participant_fields')
        # Convert the selected fields back into a dictionary with True for selected, False for not selected
        updated_required_fields = {field: field in selected_fields for field in required_fields.keys()}
        reglament_lt = request.POST.get('reglament_lt')
        reglament_en = request.POST.get('reglament_en')
        registration_deadline = request.POST.get('registration_deadline')
        payment_project_id = request.POST.get('payment_project_id')
        payment_password = request.POST.get('payment_password')
        event_result_link = request.POST.get('event_result_link')

        # Update the event instance with the new data
        event.name = name
        event.required_participant_fields = json.dumps(updated_required_fields)
        event.reglament_lt = reglament_lt
        event.reglament_en = reglament_en
        event.registration_deadline = registration_deadline if registration_deadline else None
        event.payment_project_id = payment_project_id
        event.payment_password = payment_password
        event.event_result_link = event_result_link

        # Save the updated event
        event.save()

        # Redirect to the event detail page after saving
        return redirect('event_detail', event_id=event_id)
    else:
        # Render the event details page with the event object and required fields
        return render(request, 'api/edit_event.html', {'event': event, 'required_fields': required_fields})