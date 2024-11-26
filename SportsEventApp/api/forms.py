from django import forms
from .models import Event, Group, RaceDistance

# Event form
REQUIRED_FIELDS_CHOICES = [
    ('vardas', 'Vardas'),
    ('pavarde', 'Pavardė'),
    ('gimimo_metai', 'Gimimo metai'),
    ('lytis', 'Lytis'),
    ('el_pastas', 'El. paštas'),
    ('salis', 'Šalis'),
    ('miestas', 'Miestas'),
    ('klubas', 'Klubas'),
    ('marskineliu_dydis', 'Marškinėlių dydis'),
    ('telefonas', 'Telefonas'),
    ('sportident', 'SportIdent'),
]


class EventForm(forms.ModelForm):
    required_fields = forms.MultipleChoiceField(
        choices=REQUIRED_FIELDS_CHOICES,  # Čia pateikiami pasirinkimai checkbox
        widget=forms.CheckboxSelectMultiple,  # Valdiklis, kuris rodo checkbox
        label="Bėgimui reikalingi laukeliai",  # Lauko pavadinimas
    )

    class Meta:
        model = Event
        fields = ['title', 'required_fields', 'lt_regulations', 'en_regulations', 'registration_deadline', 'logo']
        labels = {
            'title': 'Bėgimo pavadinimas',
        }

# Grupės forma
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'year_from', 'year_to', 'gender_male', 'gender_female', 'sorting_number']




class RaceDistanceForm(forms.ModelForm):
    class Meta:
        model = RaceDistance
        fields = ['name_lt', 'name_en', 'groups', 'price', 'additional_price']
        widgets = {
            'groups': forms.SelectMultiple(attrs={'size': 5}),
        }
