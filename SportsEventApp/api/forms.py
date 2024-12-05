from django import forms
from .models import Participant, Event, Distance, EventDistanceAssociation

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

    reglament_lt = forms.CharField(required=False, max_length=500, label='Reglamentas LT', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite reglamento nuorodą LT'}))
    reglament_en = forms.CharField(required=False, max_length=500, label='Reglamentas EN', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite reglamento nuorodą EN'}))

    payment_project_id = forms.CharField(required=False, max_length=255, label='Payment Project ID', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite mokėjimo projekto ID'}))
    payment_password = forms.CharField(required=False, max_length=255, label='Payment Password', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite mokėjimo slaptažodi'}))
    event_result_link = forms.CharField(required=False, max_length=500, label='Event Result Link', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite renginio nuoroda rodoma rezultatuose'}))

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

class ParticipantRegistrationForm(forms.ModelForm):
    gender_choices = [
        ('male', 'Vyras'),
        ('female', 'Moteris'),
    ]
    # Countries list (add all countries as necessary)
    countries = [
        ('LT', 'Lietuva'),
        ('US', 'Jungtinės Amerikos Valstijos'),
        # Add other countries as necessary
    ]
    # Dynamic Choice for Event and Distance
    event = forms.ModelChoiceField(queryset=Event.objects.all(), required=True)
    distance = forms.ModelChoiceField(queryset=Distance.objects.none(), required=True)
    gender = forms.ChoiceField(choices=gender_choices, required=True)
    country = forms.ChoiceField(choices=countries, required=True)

    # Participant Fields
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    date_of_birth = forms.DateField(widget=forms.SelectDateWidget(years=range(1900, 2025)), required=True)
    email = forms.EmailField(required=True)
    city = forms.CharField(max_length=100, required=True)
    club = forms.CharField(max_length=100, required=True)
    shirt_size = forms.CharField(max_length=10, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    comment = forms.CharField(widget=forms.Textarea, required=False)
    if_paid = forms.BooleanField(required=False)
    if_number_received = forms.BooleanField(required=False)
    if_shirt_received = forms.BooleanField(required=False)

    class Meta:
        model = Participant
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'country', 'city', 'club', 'shirt_size',
            'phone_number', 'comment', 'if_paid', 'if_number_received', 'if_shirt_received', 'event', 'distance'
        ]

    # Update the distance field dynamically based on the selected event
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'event' in self.data:
            try:
                event_id = int(self.data.get('event'))
                self.fields['distance'].queryset = Distance.objects.filter(
                    id__in=EventDistanceAssociation.objects.filter(event_id=event_id).values('distance_id')
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['distance'].queryset = self.instance.event.distances.all()


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
    club = forms.CharField(max_length=100, required=True)
    shirt_size = forms.CharField(max_length=10, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    comment = forms.CharField(widget=forms.Textarea, required=False)
    if_paid = forms.BooleanField(required=False)
    if_number_received = forms.BooleanField(required=False)
    if_shirt_received = forms.BooleanField(required=False)
    shirt_number = forms.CharField(max_length=10, required=False)  # New field for Shirt Number

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

    # Dynamically update the distance field based on the selected event
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

        if event:
            # Filter distances based on the selected event
            self.fields['distance'].queryset = Distance.objects.filter(
                id__in=EventDistanceAssociation.objects.filter(event_id=event.id).values('distance_id')
            )


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        return email

    def clean_shirt_number(self):
        shirt_number = self.cleaned_data.get('shirt_number')
        if shirt_number == '':
            return None
        return shirt_number
