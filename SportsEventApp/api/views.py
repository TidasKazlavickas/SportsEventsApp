import csv
import logging
import os
from datetime import date, datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import smart_str
from .forms import EventForm, GroupForm, DistanceForm, ParticipantForm, EmailForm
from .models import Group, Event, Distance, EventDistanceAssociation, Participant, EventParticipantAssociation, \
    DistanceParticipantAssociation, DistanceGroupAssociation, GroupParticipantAssociation
import json
from django.db.models import Q, F


@login_required
def event_list(request):
    search_query = request.GET.get('search', '')

    # Order events by newest first and NULL dates last
    events = Event.objects.all().order_by(F('event_date').desc(nulls_last=True))

    if search_query:
        events = events.filter(Q(name__icontains=search_query))

    return render(request, 'api/event_list.html', {
        'events': events,
        'search_query': search_query,
    })

def create_event(request):
    if request.method == 'POST':
        event_form = EventForm(request.POST, request.FILES)
        group_form = GroupForm(request.POST)
        distance_form = DistanceForm(request.POST)

        if 'submit_event' in request.POST and event_form.is_valid():

            event_name = event_form.cleaned_data['event_name']
            event_logo = event_form.cleaned_data['event_logo']
            reglament_lt = event_form.cleaned_data['reglament_lt']
            reglament_en = event_form.cleaned_data['reglament_en']
            registration_deadline = event_form.cleaned_data['registration_deadline']
            event_date = event_form.cleaned_data['event_date']
            payment_project_id = event_form.cleaned_data['payment_project_id']
            payment_password = event_form.cleaned_data['payment_password']
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

            # Save the logo if it's provided
            if event_logo:
                event_id = event_name.replace(" ", "_").lower()  # You can use event_name or generate the ID as needed
                event_logo_path = os.path.join(settings.MEDIA_ROOT, str(event_id) + '.jpg')  # Save the logo with the event ID

                # Save the file
                fs = FileSystemStorage()
                fs.save(event_logo_path, event_logo)

            # Creating a string that looks like JSON
            # Example: '{"Vardas": true, "Pavardė": false, "Gimimo metai": true}'
            fields_str = '{' + ', '.join(f'"{key}": {str(value).lower()}' for key, value in fields.items()) + '}'
            # Create a new Event instance and save to the database
            event = Event(
                name=event_name,
                required_participant_fields=fields_str,
                reglament_lt=reglament_lt,
                reglament_en=reglament_en,
                registration_deadline=registration_deadline,
                event_date=event_date,
                payment_project_id=payment_project_id,
                payment_password=payment_password,
            )
            event.save()
            return redirect('create_event')
        elif 'submit_group' in request.POST and group_form.is_valid():
            # Combine age_from and age_to into a dictionary and convert to JSON string
            age_data = json.dumps({
                'age_from': group_form.cleaned_data['age_from'],
                'age_to': group_form.cleaned_data['age_to']
            })
            # Determine gender based on the form's boolean fields
            if group_form.cleaned_data['male']:
                gender_data = "male"
            elif group_form.cleaned_data['female']:
                gender_data = "female"
            else:
                gender_data = None

            # Save the group data to the database
            participant_group = Group(
                name=group_form.cleaned_data['name'],
                age=age_data,
                gender=gender_data,
            )
            participant_group.save()
            return redirect('create_event')
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

            selected_groups = distance_form.cleaned_data['groups']

            for group in selected_groups:
                DistanceGroupAssociation.objects.create(distance=distance, group=group)

            selected_event = distance_form.cleaned_data['event']
            association = EventDistanceAssociation(event=selected_event, distance=distance)
            association.save()


            return redirect('create_event')
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
                age_data = json.loads(group.age)
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
    distances = Distance.objects.filter(eventdistanceassociation__event=event)
    # Assuming `distances` is a queryset of Distance objects
    groups = Group.objects.filter(
        group_associations__distance__in=distances
    ).distinct()
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

    for participant in participants:
        participant.groups = Group.objects.filter(participant_groups__participant=participant)
        participant.distance = participant.distances.first()

    return render(request, 'api/event_detail.html', {
        'event': event,
        'participants': participants,
        'distances': distances,
        'groups': groups
    })
def send_email_to_paid(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = Participant.objects.filter(events=event, if_paid=True)

    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_template = form.cleaned_data['message']

            for participant in participants:
                personalized_message = message_template.format(
                    name=participant.first_name,
                    lastname=participant.last_name,
                    distance=participant.distances.first().name_lt if participant.distances else "N/A",
                    shirt_number=participant.shirt_number,
                    event=event.name
                )

                send_mail(
                    subject,
                    personalized_message,
                    'sportorenginiailt@gmail.com',  # Replace with your sender email
                    [participant.email],
                    fail_silently=False,
                )

            return redirect('event_detail', event_id=event.id)
    else:
        form = EmailForm()

    return render(request, 'api/send_email.html', {
        'form': form,
        'event': event,
    })
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    required_fields = json.loads(event.required_participant_fields)

    if request.method == 'POST':
        name = request.POST.get('name')
        selected_fields = request.POST.getlist('required_participant_fields')
        # Convert the selected fields back into a dictionary with True for selected, False for not selected
        updated_required_fields = {field: field in selected_fields for field in required_fields.keys()}
        reglament_lt = request.POST.get('reglament_lt')
        reglament_en = request.POST.get('reglament_en')
        registration_deadline = request.POST.get('registration_deadline')
        event_date = request.POST.get('event_date')
        payment_project_id = request.POST.get('payment_project_id')
        payment_password = request.POST.get('payment_password')
        event_result_link = request.POST.get('event_result_link')

        # Update the event instance with the new data
        event.name = name
        event.required_participant_fields = json.dumps(updated_required_fields)
        event.reglament_lt = reglament_lt
        event.reglament_en = reglament_en
        event.registration_deadline = registration_deadline if registration_deadline else None
        event.event_date = event_date if event_date else None
        event.payment_project_id = payment_project_id
        event.payment_password = payment_password
        event.event_result_link = event_result_link

        event.save()

        return redirect('event_detail', event_id=event_id)
    else:
        return render(request, 'api/edit_event.html', {'event': event, 'required_fields': required_fields})

def edit_participant(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)

    event = participant.events.first()

    distance_association = DistanceParticipantAssociation.objects.filter(participant=participant).first()
    selected_distance = distance_association.distance if distance_association else None

    if request.method == 'POST':
        form = ParticipantForm(request.POST, event=event, instance=participant)  # Pass the existing participant instance here
        if form.is_valid():
            participant = form.save()  # Save the form, which updates the participant object

            if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
                EventParticipantAssociation.objects.create(event=event, participant=participant)

            selected_distance_id = request.POST.get('distance')

            selected_distance = get_object_or_404(Distance, id=selected_distance_id)

            if not DistanceParticipantAssociation.objects.filter(distance=selected_distance, participant=participant).exists():
                DistanceParticipantAssociation.objects.create(distance=selected_distance, participant=participant)

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

            if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
                EventParticipantAssociation.objects.create(event=event, participant=participant)

            selected_distance_id = request.POST.get('distance')

            selected_distance = get_object_or_404(Distance, id=selected_distance_id)

            if not DistanceParticipantAssociation.objects.filter(distance=selected_distance, participant=participant).exists():
                DistanceParticipantAssociation.objects.create(distance=selected_distance, participant=participant)

            # Calculate the participant's age
            today = date.today()
            age = today.year - participant.date_of_birth.year - ((today.month, today.day) < (participant.date_of_birth.month, participant.date_of_birth.day))

            groups = selected_distance.groups.all()

            eligible_groups = [
                group for group in groups if group.gender.lower() == participant.gender.lower()
            ]

            closest_group = None
            smallest_age_diff = None

            # Loop through the eligible groups to find the closest one based on age
            for group in eligible_groups:
                age_range = json.loads(group.age)
                if age_range['age_from'] <= age <= age_range['age_to']:
                    # Calculate the closeness of the group based on age range
                    age_diff_from = age - age_range['age_from']
                    age_diff_to = age_range['age_to'] - age
                    smallest_age_diff_group = min(age_diff_from, age_diff_to)

                    # Check if this group is closer than the previous closest
                    if smallest_age_diff is None or smallest_age_diff_group < smallest_age_diff:
                        smallest_age_diff = smallest_age_diff_group
                        closest_group = group

            if closest_group:
                GroupParticipantAssociation.objects.create(group=closest_group, participant=participant)

            # Check if 'if_paid' is selected, and if no shirt number is entered, assign one
            if request.POST.get('if_paid') == 'on' and (not form.cleaned_data.get('shirt_number')):
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
    numbers_str = distance.numbers

    # Parse the string into a dictionary
    number_range = json.loads(numbers_str)

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

    response = HttpResponse(content_type='text/csv; charset=utf-8') # UTF-8 to handle Lithuanian letters
    response['Content-Disposition'] = f'attachment; filename="participants_{event.name}.csv"'

    response.write("\ufeff")  # BOM for UTF-8

    # Create CSV writer with semicolon delimiter
    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row
    writer.writerow([smart_str(header) for header in [
        'Numeris', 'Vardas', 'Pavardė', 'Gimimo data', 'Lytis', 'Grupė' ,'El.paštas',
        'Valstybė', 'Miestas', 'Klubas', 'Distancija','Registracijos data', 'Komentaras', 'Telefonas'
    ]])

    # Write participant data
    for participant in participants:

        participant.groups = Group.objects.filter(participant_groups__participant=participant)
        writer.writerow([smart_str(value) for value in [
            participant.shirt_number or "N/A",
            participant.first_name or "N/A",
            participant.last_name or "N/A",
            participant.date_of_birth.strftime('%Y-%m-%d') if participant.date_of_birth else "N/A",
            participant.gender or "N/A",
            participant.groups.first().name or "N/A",
            participant.email or "N/A",
            participant.country or "N/A",
            participant.city or "N/A",
            participant.club or "N/A",
            participant.distances.first().name_lt or "N/A",
            participant.registration_date.strftime('%Y-%m-%d') if participant.registration_date else "N/A",
            participant.comment or "N/A",
            participant.phone_number or "N/A",
        ]])

    return response

def add_event_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        results_link = request.POST.get('results_link')
        if results_link:
            event.result_link = results_link
            event.save()
            messages.success(request, "Renginio rezultatai sėkmingai pridėti.")
            return redirect('event_detail', event_id=event_id)
        else:
            messages.error(request, "Prašome įvesti rezultatų nuorodą.")

    return render(request, 'api/add_event_results.html', {'event': event})


def upload_event_photos(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    event_folder = os.path.join(settings.MEDIA_ROOT, 'event_photos', event.name)

    # If the directory doesn't exist, create it
    if not os.path.exists(event_folder):
        os.makedirs(event_folder)

    # Handling the file upload
    if request.method == 'POST' and request.FILES.getlist('photos'):
        # Loop through the files uploaded and save them
        for photo in request.FILES.getlist('photos'):
            # Create the file path to save it locally in the event folder
            fs = FileSystemStorage(location=event_folder)
            filename = fs.save(photo.name, photo)
            file_url = fs.url(filename)

        return redirect('event_detail', event_id=event_id)

    return render(request, 'api/upload_event_photos.html', {'event': event})


def export_all_participants_csv(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Get filtered participants based on the search parameters
    participants = Participant.objects.filter(events__id=event_id)

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

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="participants_{event.name}.csv"'

    response.write("\ufeff")

    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    writer.writerow([smart_str(header) for header in [
        'Numeris', 'Vardas', 'Pavardė', 'Gimimo data', 'Lytis', 'Grupė' ,'El.paštas',
        'Valstybė', 'Miestas', 'Klubas', 'Distancija','Registracijos data', 'Komentaras', 'Telefonas'
    ]])

    for participant in participants:

        participant.groups = Group.objects.filter(participant_groups__participant=participant)
        writer.writerow([smart_str(value) for value in [
            participant.shirt_number or "N/A",
            participant.first_name or "N/A",
            participant.last_name or "N/A",
            participant.date_of_birth.strftime('%Y-%m-%d') if participant.date_of_birth else "N/A",
            participant.gender or "N/A",
            participant.groups.first().name or "N/A",
            participant.email or "N/A",
            participant.country or "N/A",
            participant.city or "N/A",
            participant.club or "N/A",
            participant.distances.first().name_lt or "N/A",
            participant.registration_date.strftime('%Y-%m-%d') if participant.registration_date else "N/A",
            participant.comment or "N/A",
            participant.phone_number or "N/A",
        ]])

    return response

def custom_logout(request):
    logout(request)
    return redirect('login')

def show_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    result_link = event.result_link
    return render(request, 'frontend/show_results.html', {'result_link': result_link})


def upload_participants(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    errors = []

    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, "Please upload a file.")
            return redirect('upload_participants', event_id=event_id)

        csv_file = request.FILES['file']
        try:
            # Decode file and read rows
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            csv_reader = csv.DictReader(decoded_file, delimiter=';')  # Use semicolon as delimiter

            # Normalize column names
            if csv_reader.fieldnames:
                csv_reader.fieldnames = [field.strip() for field in csv_reader.fieldnames]


            # Check for missing columns
            required_columns = [
                'Vardas', 'Pavardė', 'Gimimo data', 'Lytis',
                'El.paštas', 'Valstybė', 'Miestas', 'Klubas',
                'Telefonas', 'Komentaras', 'Registracijos data', 'Distancija'
            ]
            missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]
            if missing_columns:
                errors.append(f"Missing columns: {', '.join(missing_columns)}")

                return redirect('upload_participants', event_id=event_id)

        except UnicodeDecodeError as e:

            messages.error(request, "There was an issue with file encoding. Please upload a valid CSV file.")
            return redirect('upload_participants', event_id=event_id)

        # Process each row in the CSV file
        for row in csv_reader:


            # Check for 'Distancija' column
            selected_distance_name = row.get('Distancija', '').strip()  # Strip spaces
            if not selected_distance_name:
                errors.append("Missing 'Distancija' column or value.")

                continue



            try:
                selected_distance = Distance.objects.get(
                    eventdistanceassociation__event=event,
                    name_lt=selected_distance_name
                )


            except Distance.DoesNotExist:
                errors.append(f"Distance '{selected_distance_name}' not found for this event.")
                continue

            # Create participant record
            try:
                participant = Participant.objects.create(
                    first_name=row['Vardas'].strip(),
                    last_name=row['Pavardė'].strip(),
                    date_of_birth=row['Gimimo data'].strip(),
                    gender=row['Lytis'].strip(),
                    email=row['El.paštas'].strip(),
                    country=row['Valstybė'].strip(),
                    city=row['Miestas'].strip(),
                    club=row['Klubas'].strip(),
                    phone_number=row['Telefonas'].strip(),
                    comment=row['Komentaras'].strip(),
                    registration_date=row['Registracijos data'].strip(),
                )


                # Create associations
                EventParticipantAssociation.objects.get_or_create(event=event, participant=participant)
                DistanceParticipantAssociation.objects.get_or_create(distance=selected_distance, participant=participant)

                # Calculate the participant's age
                today = date.today()
                participant_date_of_birth = datetime.strptime(participant.date_of_birth, "%Y-%m-%d").date()
                age = today.year - participant_date_of_birth.year - ((today.month, today.day) < (participant_date_of_birth.month, participant_date_of_birth.day))

                groups = selected_distance.groups.all()

                eligible_groups = [
                    group for group in groups if group.gender.lower() == participant.gender.lower()
                ]

                closest_group = None
                smallest_age_diff = None

                # Loop through the eligible groups to find the closest one based on age
                for group in eligible_groups:
                    age_range = json.loads(group.age)
                    if age_range['age_from'] <= age <= age_range['age_to']:
                        # Calculate the closeness of the group based on age range
                        age_diff_from = age - age_range['age_from']
                        age_diff_to = age_range['age_to'] - age
                        smallest_age_diff_group = min(age_diff_from, age_diff_to)

                        # Check if this group is closer than the previous closest
                        if smallest_age_diff is None or smallest_age_diff_group < smallest_age_diff:
                            smallest_age_diff = smallest_age_diff_group
                            closest_group = group

                if closest_group:
                    GroupParticipantAssociation.objects.create(group=closest_group, participant=participant)

                next_available_number = get_next_available_number(selected_distance)

                # Only assign if a valid number is available
                if next_available_number is not None:
                    participant.shirt_number = next_available_number
                    participant.if_paid = True
                    participant.save()
            except KeyError as ke:

                errors.append(f"Missing field: {ke}")
            except Exception as e:

                errors.append(f"Unexpected error: {str(e)}")

        # Handle any errors that occurred during processing
        if errors:

            messages.error(request, "Errors occurred during the upload process.")
            return redirect('upload_participants', event_id=event_id)

        # If successful
        messages.success(request, "Participants uploaded successfully.")
        return redirect('event_detail', event_id=event_id)

    return render(request, 'api/upload_participants.html', {'event': event})
