from django.shortcuts import render, redirect
from .forms import EventForm, GroupForm, DistanceForm
from .models import Group, Event
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

            # Create a new Event instance and save to the database
            event = Event(
                name=event_name,
                required_participant_fields=required_participant_fields,  # Save as a string resembling JSON
                reglament_lt=reglament_lt,
                reglament_en=reglament_en
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
        elif 'submit_distance' in request.POST and event_form.is_valid():
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
