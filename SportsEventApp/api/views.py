from django.shortcuts import render, redirect
from .forms import EventForm, GroupForm, DistanceForm
from .models import Group, Event, Distance
import json

def index(request):
    return render(request, 'api/index.html')

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

            # Create a new Event instance and save to the database
            event = Event(
                name=event_name,
                required_participant_fields=required_participant_fields,  # Save as a string resembling JSON
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

