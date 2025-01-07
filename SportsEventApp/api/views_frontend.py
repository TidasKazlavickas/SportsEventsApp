import os
from datetime import date
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from paypalrestsdk import Payment
from django.http import HttpResponseRedirect, HttpResponse
from .paypal_config import paypalrestsdk
from django.urls import reverse
from api.forms import ParticipantForm, UserProfileForm
from api.models import Event, Distance, DistanceParticipantAssociation, GroupParticipantAssociation, \
    EventParticipantAssociation, Participant, UserEventDistance
from django.conf import settings
import json
from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from api.views import get_next_available_number
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile


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

    # Get participant for authenticated user, if any
    participant = None
    if request.user.is_authenticated:
        # Check if the user has a profile, and fetch the participant associated with the user
        participant = Participant.objects.filter(user=request.user).first()

    # Initialize the form with the event and user profile (if any)
    form = ParticipantForm(request.POST or None, event=event, user=request.user if request.user.is_authenticated else None, instance=participant)

    # Dynamically hide fields based on the event's configuration
    for label, field_name in LABEL_TO_FIELD.items():
        if field_name != "distance":
            if config_dict.get(label, False) is False:
                if field_name in form.fields:
                    form.fields[field_name].widget = forms.HiddenInput()  # Hide the field
                    form.fields[field_name].required = False

    if form.is_valid():
        participant = form.save(commit=False)  # Don't save to DB yet

        # Link the participant to the logged-in user (if any)
        if request.user.is_authenticated:
            participant.user = request.user  # Associate participant with user

        # Register participant with if_paid as False
        participant.if_paid = False  # Initially set to False

        # Handle empty shirt_number
        if not participant.shirt_number:
            participant.shirt_number = None

        participant.save()  # Save the participant now

        # Create Event-Participant Association
        if not EventParticipantAssociation.objects.filter(event=event, participant=participant).exists():
            EventParticipantAssociation.objects.create(event=event, participant=participant)

        # Process selected distance
        selected_distance_id = request.POST.get('distance')
        selected_distance = get_object_or_404(Distance, id=selected_distance_id)

        if not DistanceParticipantAssociation.objects.filter(distance=selected_distance, participant=participant).exists():
            DistanceParticipantAssociation.objects.create(distance=selected_distance, participant=participant)

        # Create or update UserEventDistance entry (only for authenticated users)
        if request.user.is_authenticated:
            UserEventDistance.objects.get_or_create(
                user=request.user,
                event=event,
                distance=selected_distance
            )

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

        if payment_method == 'online_payment':
            # Create PayPal Payment
            payment = Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": request.build_absolute_uri(reverse('paypal_execute', args=[participant_id, selected_distance.id])),
                    "cancel_url": request.build_absolute_uri(reverse('payment_options', args=[participant_id, event_id, selected_distance.id]))
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Registration for {event.name}",
                            "sku": "001",
                            "price": selected_distance.price,
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": selected_distance.price,
                        "currency": "USD"
                    },
                    "description": f"Registration for {event.name}"
                }]
            })

            if payment.create():
                # Redirect to PayPal for payment
                for link in payment.links:
                    if link.rel == "approval_url":
                        return redirect(link.href)
            else:
                return render(request, 'frontend/payment_error.html', {"error": "Error creating PayPal payment."})

        elif payment_method == 'cash_payment':
            participant.if_paid = False  # Ensure not marked as paid
            participant.save()
            return redirect('payment_pending', participant_id=participant_id)

    return render(request, 'frontend/payment_options.html', {'participant': participant, 'event': event})

def payment_success(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    return render(request, 'frontend/payment_success.html', {'participant': participant})

def payment_pending(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    return render(request, 'frontend/payment_pending.html', {'participant': participant})

def paypal_execute(request, participant_id, distance_id):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        participant = get_object_or_404(Participant, id=participant_id)
        participant.if_paid = True
        participant.save()

        distance = get_object_or_404(Distance, id=distance_id)
        if not participant.shirt_number:
            next_available_number = get_next_available_number(distance)
            if next_available_number:
                participant.shirt_number = next_available_number
                participant.save()

        send_confirmation_email(participant)

        return redirect('payment_success', participant_id=participant_id)
    else:
        return HttpResponse("Payment execution failed.", status=400)

def send_confirmation_email(participant):
    event = participant.events.first()
    if not event:
        raise ValueError("Participant is not associated with any event.")

    distance = participant.distances.first()

    subject = "Patvirtinimas: Jūsų registracija į renginį sėkminga"
    message = (
        f"Gerb. {participant.first_name} {participant.last_name},\n\n"
        f"Jūs sėkmingai užsiregistravote į sporto renginį: {event.name}.\n"
        f"Renginio data: {event.event_date.strftime('%Y-%m-%d')}.\n"
        f"Distancija: {distance.name_lt if distance else 'N/A'}.\n"
        f"Jūsų marškinėlių numeris: {participant.shirt_number}.\n\n"
        f"Laukiame Jūsų renginyje!\n\n"
        f"Pagarbiai,\nSporto renginių komanda"
    )

    send_mail(
        subject,
        message,
        'sportorenginiailt@gmail.com',
        [participant.email],
        fail_silently=False,
    )

def about_us(request):
    return render(request, 'frontend/about_us.html')

def privacy_policy(request):
    return HttpResponseRedirect('/static/pdf/privatumo_politikos_taisykles.pdf')

def contact(request):
    return render(request, 'frontend/contacts.html')

@login_required
def user_events(request):
    # Get all UserEventDistance records associated with the logged-in user
    user_event_distances = UserEventDistance.objects.filter(user=request.user)

    return render(request, 'frontend/user_events.html', {'user_event_distances': user_event_distances})



class UserLoginView(LoginView):
    template_name = 'frontend/user_login.html'

    def get_success_url(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return '/admin/'  # Redirect admins to the admin panel
        return super().get_success_url()  # Redirect normal users to their default page

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = UserCreationForm()

    return render(request, 'frontend/register.html', {'form': form})

class CustomLoginView(LoginView):
    def get_success_url(self):
        # Redirect admins to /events/, normal users to /events-front/
        if self.request.user.is_staff or self.request.user.is_superuser:
            return '/events/'
        return '/events-front/'

    def form_valid(self, form):
        # Ensure a UserProfile is created if it doesn't exist for the user
        if not hasattr(self.request.user, 'profile'):
            UserProfile.objects.create(user=self.request.user)
        return super().form_valid(form)

def save_user_profile(user):
    if not hasattr(user, 'profile'):
        user_profile = UserProfile.objects.create(user=user)
    else:
        user_profile = user.profile
    return user_profile

@login_required
def edit_profile(request):
    user = request.user

    # Check if the profile exists for the user; if not, create it
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)

    profile = user.profile  # Get the user's profile

    if request.method == 'POST':
        # Handle the form submission to update the profile
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('user_profile', user_id=user.id)  # Redirect to the profile page
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'frontend/edit_profile.html', {'form': form, 'profile': profile})

@login_required
def profile_view(request, user_id):
    # Retrieve the user by the provided user_id
    user = get_object_or_404(User, id=user_id)
    # Pass the user object to the template
    return render(request, 'frontend/profile.html', {'user': user})