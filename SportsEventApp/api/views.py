import csv
from datetime import date

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import smart_str

from .forms import EventForm, GroupForm, DistanceForm, ParticipantRegistrationForm, ParticipantForm
from .models import Group, Event, Distance, EventDistanceAssociation, Participant, EventParticipantAssociation, \
    DistanceParticipantAssociation, DistanceGroupAssociation, GroupParticipantAssociation
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
            # Combine numbers_from and numbers_to into dictionaries
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
                numbers=numbers_data,  # Store JSON string
                special_numbers=special_numbers_data,  # Store JSON string
                price=distance_form.cleaned_data['price'],
                price_extra=distance_form.cleaned_data['extra_price'],
                price_extra_date=distance_form.cleaned_data['extra_price_date'],
                if_race=distance_form.cleaned_data['if_race'],
                race_participant_count=participant_count
            )
            distance.save()

            # Now, create associations for each selected group
            selected_groups = distance_form.cleaned_data['groups']  # Retrieve the selected groups

            for group in selected_groups:
                DistanceGroupAssociation.objects.create(distance=distance, group=group)

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
    participants = Participant.objects.filter(events__id=event_id)

    # Filter by search query parameters
    search_first_name = request.GET.get('search_first_name', '')
    search_last_name = request.GET.get('search_last_name', '')
    search_email = request.GET.get('search_email', '')
    search_country = request.GET.get('search_country', '')
    search_status = request.GET.get('search_status', '')
    search_number = request.GET.get('search_number', '')
    search_gender = request.GET.get('search_gender', '')
    search_club = request.GET.get('search_club', '')
    search_group = request.GET.get('search_group', '')
    search_distance = request.GET.get('search_distance', '')
    number_received = request.GET.get('number_received', '')
    shirt_assigned = request.GET.get('shirt_assigned', '')

    # Apply filters
    if search_first_name:
        participants = participants.filter(first_name__icontains=search_first_name)

    if search_last_name:
        participants = participants.filter(last_name__icontains=search_last_name)

    if search_email:
        participants = participants.filter(email__icontains=search_email)

    if search_country:
        participants = participants.filter(country__icontains=search_country)

    if search_status == "paid":
        participants = participants.filter(if_paid=True)
    elif search_status == "not_paid":
        participants = participants.filter(if_paid=False)

    if search_number:
        participants = participants.filter(id=search_number)

    if search_gender:
        participants = participants.filter(gender=search_gender)

    if search_club:
        participants = participants.filter(club__icontains=search_club)

    if search_group:
        participants = participants.filter(events__group=search_group)

    if search_distance:
        participants = participants.filter(distances__id=search_distance)

    if number_received == "yes":
        participants = participants.filter(if_number_received=True)

    if shirt_assigned == "yes":
        participants = participants.filter(if_shirt_received=True)

    # Retrieve the associated groups for each participant
    for participant in participants:
        participant.groups = Group.objects.filter(participant_groups__participant=participant)

    return render(request, 'api/event_detail.html', {
        'event': event,
        'participants': participants,
    })

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

def edit_participant(request, participant_id):
    # Retrieve the existing participant or return 404 if not found
    participant = get_object_or_404(Participant, id=participant_id)

    # Retrieve the associated event (assuming the participant has at least one event)
    event = participant.events.first()

    # Retrieve the associated distance for the participant, if any
    distance_association = DistanceParticipantAssociation.objects.filter(participant=participant).first()
    selected_distance = distance_association.distance if distance_association else None

    if request.method == 'POST':
        form = ParticipantForm(request.POST, event=event, instance=participant)  # Pass the existing participant instance here
        if form.is_valid():
            participant = form.save()  # Save the form, which updates the participant object

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

            # Check if 'if_paid' is selected, and if no shirt number is entered, assign one
            if request.POST.get('if_paid') == 'on' and not participant.shirt_number:
                next_available_number = get_next_available_number(selected_distance)

                # Only assign if a valid number is available
                if next_available_number is not None:
                    participant.shirt_number = next_available_number
                    participant.save()

            return redirect('event_detail', event_id=event.id)
    else:
        # Populate the form with the current participant data and selected distance
        form = ParticipantForm(event=event, instance=participant)
        if selected_distance:
            form.fields['distance'].initial = selected_distance.id

    return render(request, 'api/edit_participant.html', {'form': form, 'participant': participant, 'event': event})

def delete_participant(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    event_id = participant.events.first().id  # Get the event associated with the participant
    participant.delete()  # Delete the participant
    return redirect('event_detail', event_id=event_id)

def add_participant(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = ParticipantForm(request.POST, event=event)
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

            return redirect('event_detail', event_id=event_id)

    else:
        form = ParticipantForm(event=event)

    return render(request, 'api/add_participant.html', {'event': event, 'form': form})

def get_next_available_number(distance):
    # Assuming 'distance.numbers' is a string containing JSON-like data
    numbers_str = distance.numbers  # The string, e.g., '{"numbers_from": 100, "numbers_to": 999}'

    # Parse the string into a dictionary
    number_range = json.loads(numbers_str)

    # Now you can safely access the fields
    numbers_from = number_range.get("numbers_from")
    numbers_to = number_range.get("numbers_to")

    if numbers_from is None or numbers_to is None:
        raise ValueError("Invalid number range in the distance.")

    # Get all used numbers in this distance range
    used_numbers = DistanceParticipantAssociation.objects.filter(distance=distance).values_list('participant__shirt_number', flat=True)

    # Generate a set of all possible numbers in the range
    all_possible_numbers = set(range(numbers_from, numbers_to + 1))

    # Find the unused numbers
    available_numbers = all_possible_numbers - set(used_numbers)

    # Return the first available number, or None if no numbers are available
    return min(available_numbers) if available_numbers else None

def export_participants_csv(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Get filtered participants based on the search parameters
    participants = Participant.objects.filter(events__id=event_id, if_paid=True)

    # Get filter parameters from the request
    search_name = request.GET.get('search_name', '')
    search_country = request.GET.get('search_country', '')
    search_city = request.GET.get('search_city', '')
    search_club = request.GET.get('search_club', '')
    search_gender = request.GET.get('search_gender', '')

    if search_name:
        participants = participants.filter(
            first_name__icontains=search_name) | participants.filter(last_name__icontains=search_name)

    if search_country:
        participants = participants.filter(country__icontains=search_country)

    if search_city:
        participants = participants.filter(city__icontains=search_city)

    if search_club:
        participants = participants.filter(club__icontains=search_club)

    if search_gender:
        participants = participants.filter(gender=search_gender)

    # Create CSV response with UTF-8 encoding to handle Lithuanian characters
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="participants_{event.name}.csv"'

    # Adding BOM to ensure proper encoding in Excel
    response.write("\ufeff")  # BOM for UTF-8

    # Create CSV writer with semicolon delimiter
    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row
    writer.writerow([smart_str(header) for header in [
        'Numeris', 'Vardas', 'Pavardė', 'Gimimo data', 'Lytis', 'El.paštas',
        'Valstybė', 'Miestas', 'Klubas', 'Registracijos data', 'Nr. išduotas?',
        'Marškinėliai priskirti', 'Dydis', 'Komentaras', 'Mokestis', 'Telefonas', 'Ar sumokėjęs'
    ]])

    # Write participant data
    for participant in participants:
        writer.writerow([smart_str(value) for value in [
            participant.shirt_number or "N/A",
            participant.first_name or "N/A",
            participant.last_name or "N/A",
            participant.date_of_birth.strftime('%Y-%m-%d') if participant.date_of_birth else "N/A",
            participant.gender or "N/A",
            participant.email or "N/A",
            participant.country or "N/A",
            participant.city or "N/A",
            participant.club or "N/A",
            participant.registration_date.strftime('%Y-%m-%d') if participant.registration_date else "N/A",
            'Taip' if participant.if_number_received else 'Ne',
            'Taip' if participant.if_shirt_received else 'Ne',
            participant.shirt_size or "N/A",
            participant.comment or "N/A",
            'Taip' if participant.if_paid else 'Ne',
            participant.phone_number or "N/A",  # This is now in the correct column
            'Taip' if participant.if_paid else 'Ne'  # Correct column for "Ar sumokėjęs"
        ]])

    return response
