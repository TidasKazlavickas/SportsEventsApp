from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.forms import modelformset_factory
from .models import Event, Group, RaceDistance
from .forms import EventForm, GroupForm, RaceDistanceForm


@api_view(['GET'])
def return_one(request):
    return Response({"result": 1})

@api_view(['GET'])
def return_two(request):
    return Response({"result": 2})

@api_view(['GET'])
def sum_numbers(request):
    # Get query parameters 'a' and 'b' from the request URL
    try:
        a = int(request.query_params.get('a', 0))
        b = int(request.query_params.get('b', 0))
        return Response({"result": a + b})
    except (ValueError, TypeError):
        return Response({"error": "Invalid or missing parameters. Please provide integers 'a' and 'b'."}, status=400)

def db_health_check(request):
    try:
        # Attempt to connect to the default database
        connection = connections['default']
        connection.ensure_connection()
        return JsonResponse({"status": "success", "message": "Database connection successful!"}, status=200)
    except OperationalError as e:
        return JsonResponse({"status": "error", "message": "Database connection failed!", "error": str(e)}, status=500)

def index(request):
    return render(request, 'api/index.html')

from django.shortcuts import render


RUNNING_EVENTS = [
    {"name": "Vilniaus maratonas 2023"},
    {"name": "Kauno bėgimas 2023"},
    {"name": "Druskininkų naktinis bėgimas 2024"},
    {"name": "Klaipėdos pavasario bėgimas 2024"},
]
# Sukuriame 'event_list' funkciją, kuri rodys renginių sąrašą
def event_list(request):
    query = request.GET.get('q', '')  # Gauname paieškos frazę
    filtered_events = [
        event for event in RUNNING_EVENTS if query.lower() in event["name"].lower()
    ] if query else RUNNING_EVENTS

    return render(request, 'event_list.html', {
        "events": filtered_events,
        "query": query,
    })


def create_event(request):
    # Grupės formset
    GroupFormSet = modelformset_factory(Group, form=GroupForm, extra=1, can_delete=True)

    if request.method == 'POST':
        # Inicijuojame visas formas su POST ir FILES duomenimis
        event_form = EventForm(request.POST, request.FILES)
        group_formset = GroupFormSet(request.POST)
        distance_form = RaceDistanceForm(request.POST)

        if event_form.is_valid() and group_formset.is_valid() and distance_form.is_valid():
            # Išsaugome renginį
            event = event_form.save()

            # Išsaugome grupes
            groups = group_formset.save(commit=False)
            for group in groups:
                group.save()
            for deleted_group in group_formset.deleted_objects:
                deleted_group.delete()

            # Išsaugome bėgimo distanciją
            distance = distance_form.save(commit=False)
            distance.event = event
            distance.save()
            distance_form.save_m2m()  # Išsaugome ManyToMany laukus

            return redirect('event_list')  # Nukreipiame į renginių sąrašą

    else:
        # GET užklausa: tuščios formos
        event_form = EventForm()
        group_formset = GroupFormSet(queryset=Group.objects.none())
        distance_form = RaceDistanceForm()

    return render(request, 'create_event.html', {
        'event_form': event_form,
        'group_formset': group_formset,
        'distance_form': distance_form,
    })
