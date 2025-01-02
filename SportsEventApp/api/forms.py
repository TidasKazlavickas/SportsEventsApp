import json

from django import forms
from .models import Participant, Event, Distance, EventDistanceAssociation, Group, DistanceGroupAssociation, UserProfile


class EventForm(forms.Form):
    event_name = forms.CharField(required=False, max_length=200, label='Bėgimo pavadinimas', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite bėgimo pavadinimą'}))

    # Checkboxes for Required Fields
    required_participant_fields = forms.CharField(widget=forms.HiddenInput(), required=False)
    is_name_required = forms.BooleanField(required=False, label='Vardas')
    is_surname_required = forms.BooleanField(required=False, label='Pavardė')
    is_birth_year_required = forms.BooleanField(required=False, label='Gimimo metai')
    is_gender_required = forms.BooleanField(required=False, label='Lytis')
    is_email_required = forms.BooleanField(required=False, label='El. paštas')
    is_city_required = forms.BooleanField(required=False, label='Miestas')
    is_club_required = forms.BooleanField(required=False, label='Klubas')
    is_shirt_size_required = forms.BooleanField(required=False, label='Marškinėlių dydis')
    is_phone_required = forms.BooleanField(required=False, label='Telefonas')
    is_sportident_required = forms.BooleanField(required=False, label='Sportident')
    registration_deadline = forms.DateField(required=False,label='Registracijos pabaigos data',widget=forms.DateInput(attrs={'type': 'date'}))
    event_date = forms.DateField(required=False, label='Renginio data',widget=forms.DateInput(attrs={'type': 'date'}))
    reglament_lt = forms.CharField(required=False, max_length=500, label='Reglamentas LT', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite reglamento nuorodą LT'}))
    reglament_en = forms.CharField(required=False, max_length=500, label='Reglamentas EN', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite reglamento nuorodą EN'}))

    payment_project_id = forms.CharField(required=False, max_length=255, label='Payment Project ID', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite mokėjimo projekto ID'}))
    payment_password = forms.CharField(required=False, max_length=255, label='Payment Password', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite mokėjimo slaptažodi'}))
    event_logo = forms.ImageField(required=False, label='Įkelti renginio logotipą')

class EmailForm(forms.Form):
    subject = forms.CharField(max_length=255, label="Tema")
    message = forms.CharField(widget=forms.Textarea, label="Turinys")

class GroupForm(forms.Form):
    name = forms.CharField(required=False, max_length=100, label='Pavadinimas')
    age_from = forms.IntegerField(required=False, label='Metai nuo')
    age_to = forms.IntegerField(required=False, label='Metai iki')
    male = forms.BooleanField(required=False, label='Vyrai')
    female = forms.BooleanField(required=False, label='Moterys')

class DistanceForm(forms.Form):
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        empty_label="Select an event",
        label='Event'
    )
    name_lt = forms.CharField(required=False, max_length=100, label='Pavadinimas LT')
    name_en = forms.CharField(required=False, max_length=100, label='Pavadinimas EN')
    numbers_from = forms.IntegerField(required=False, label='Numeriai nuo')
    numbers_to = forms.IntegerField(required=False, label='Numeriai iki')
    extra_numbers_from = forms.IntegerField(required=False, label='Papildomi numeriai nuo')
    extra_numbers_to = forms.IntegerField(required=False, label='Papildomi numeriai iki')
    price = forms.CharField(required=False, max_length=10, label='Kaina')
    extra_price = forms.CharField(required=False, max_length=10, label='Papildoma kaina')
    extra_price_date = forms.DateField(required=False, label="Data nuo")
    if_race = forms.BooleanField(required=False, label='Estafetė?')
    race_participant_count = forms.IntegerField(required=False, label='Dalyvių skaičius')
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(),widget=forms.SelectMultiple(attrs={'size': 10}),required=False,label='Groups')

def save(self):
    # Save the Distance instance
    distance_data = self.cleaned_data
    distance = Distance.objects.create(
        name_lt=distance_data['name_lt'],
        name_en=distance_data['name_en'],
        numbers=json.dumps({
            'from': distance_data['numbers_from'],
            'to': distance_data['numbers_to'],
            'extra_from': distance_data['extra_numbers_from'],
            'extra_to': distance_data['extra_numbers_to']
        }),
        special_numbers="",
        price=distance_data['price'],
        price_extra=distance_data['extra_price'],
        price_extra_date=distance_data['extra_price_date'],
        if_race=distance_data['if_race'],
        race_participant_count=distance_data['race_participant_count'],
    )

    # Create associations between the selected groups and the newly created distance
    for group in distance_data['groups']:
        DistanceGroupAssociation.objects.create(distance=distance, group=group)
    return distance

class ParticipantForm(forms.ModelForm):
    gender_choices = [
        ('male', 'Vyras'),
        ('female', 'Moteris'),
        ('other', 'Kita'),
    ]

    # Participant Fields
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    date_of_birth = forms.DateField(widget=forms.SelectDateWidget(years=range(1900, 2025)), required=True)
    email = forms.EmailField(required=True)
    city = forms.CharField(max_length=100, required=True)
    club = forms.CharField(max_length=100, required=False)
    shirt_size = forms.CharField(max_length=10, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    comment = forms.CharField(widget=forms.Textarea, required=False)
    if_paid = forms.BooleanField(required=False)
    if_number_received = forms.BooleanField(required=False)
    if_shirt_received = forms.BooleanField(required=False)
    shirt_number = forms.CharField(max_length=10, required=False)

    # Allow free text input for country
    country = forms.CharField(max_length=100, required=True)

    # Dynamic Distance field based on the selected event
    distance = forms.ModelChoiceField(queryset=Distance.objects.none(), required=True)

    class Meta:
        model = Participant
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'country', 'city', 'club', 'shirt_size',
            'phone_number', 'comment', 'if_paid', 'if_number_received', 'if_shirt_received', 'shirt_number', 'distance'
        ]
        labels = {
            'first_name': 'Vardas',
            'last_name': 'Pavardė',
            'date_of_birth': 'Gimimo data',
            'gender': 'Lytis',
            'email': 'El. paštas',
            'country': 'Valstybė',
            'city': 'Miestas',
            'club': 'Klubas',
            'shirt_size': 'Marškinėlių dydis',
            'phone_number': 'Telefonas',
            'comment': 'Komentaras',
            'if_paid': 'Sumokėjęs',
            'if_number_received': 'Nr. Išduotas',
            'if_shirt_received': 'Marškiniai išduoti',
            'shirt_number': 'Numeris',
            'distance': 'Distancija',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('Male', 'Vyras'), ('Female', 'Moteris'), ('Other', 'Kita')]),
            'comment': forms.Textarea(attrs={'rows': 3}),
            'distance': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)  # Get the event from kwargs
        user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)

        if event:
            # Filter distances based on the selected event
            self.fields['distance'].queryset = Distance.objects.filter(
                id__in=EventDistanceAssociation.objects.filter(event_id=event.id).values('distance_id')
            )

        if user:
            # Pre-fill fields if the user has an associated participant record
            participant = Participant.objects.filter(user=user).first()
            if participant:
                for field in self.fields:
                    if hasattr(participant, field):
                        self.fields[field].initial = getattr(participant, field)

            user_profile = user.profile
            self.fields['first_name'].initial = user_profile.first_name
            self.fields['last_name'].initial = user_profile.last_name
            self.fields['email'].initial = user_profile.email
            self.fields['city'].initial = user_profile.city
            self.fields['club'].initial = user_profile.club
            self.fields['shirt_size'].initial = user_profile.shirt_size
            self.fields['phone_number'].initial = user_profile.phone_number
            self.fields['country'].initial = user_profile.country
            self.fields['gender'].initial = user_profile.gender
            self.fields['date_of_birth'].initial = user_profile.date_of_birth


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'country', 'city', 'club', 'shirt_size', 'phone_number']
        labels = {
            'first_name': 'Vardas',
            'last_name': 'Pavardė',
            'date_of_birth': 'Gimimo data',
            'gender': 'Lytis',
            'email': 'El. paštas',
            'country': 'Valstybė',
            'city': 'Miestas',
            'club': 'Klubas',
            'shirt_size': 'Marškinėlių dydis',
            'phone_number': 'Telefonas',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('male', 'Vyras'), ('female', 'Moteris'), ('other', 'Kita')]),
        }

def clean_shirt_number(self):
        shirt_number = self.cleaned_data.get('shirt_number')
        if shirt_number == '':
            return None
        return shirt_number
