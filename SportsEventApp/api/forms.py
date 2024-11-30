from django import forms

class EventForm(forms.Form):
    event_name = forms.CharField(required=False, max_length=200, label='Bėgimo pavadinimas', widget=forms.TextInput(attrs={'placeholder': 'Įrašykite bėgimo pavadinimą'}))

    # Checkboxes for Required Fields
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

    def clean_required_participant_fields(self):
        # Construct the "JSON-like" string from the form data
        fields = {
            'Vardas': self.cleaned_data.get('is_name_required'),
            'Pavardė': self.cleaned_data.get('is_surname_required'),
            'Gimimo metai': self.cleaned_data.get('is_birth_year_required'),
            'Lytis': self.cleaned_data.get('is_gender_required'),
            'El. paštas': self.cleaned_data.get('is_email_required'),
            'Miestas': self.cleaned_data.get('is_city_required'),
            'Klubas': self.cleaned_data.get('is_club_required'),
            'Marškinėlių dydis': self.cleaned_data.get('is_shirt_size_required'),
            'Telefonas': self.cleaned_data.get('is_phone_required'),
            'Sportident': self.cleaned_data.get('is_sportident_required'),
        }

        # Creating a string that looks like JSON, but is a plain string
        # Example: '{"Vardas": true, "Pavardė": false, "Gimimo metai": true}'
        fields_str = '{' + ', '.join(f'"{key}": {str(value).lower()}' for key, value in fields.items()) + '}'

        return fields_str

class GroupForm(forms.Form):
    name = forms.CharField(required=False, max_length=100, label='Pavadinimas')
    age_from = forms.IntegerField(required=False, label='Metai nuo')
    age_to = forms.IntegerField(required=False, label='Metai iki')
    male = forms.BooleanField(required=False, label='Vyrai')
    female = forms.BooleanField(required=False, label='Moterys')

class DistanceForm(forms.Form):
    name_lt = forms.CharField(required=False, max_length=100, label='Pavadinimas LT')
    name_en = forms.CharField(required=False, max_length=100, label='Pavadinimas EN')
    numbers_from = forms.IntegerField(required=False, label='Numeriai nuo')
    numbers_to = forms.IntegerField(required=False, label='Numeriai iki')
    extra_numbers_from = forms.IntegerField(required=False, label='Papildomi numeriai nuo')
    extra_numbers_to = forms.IntegerField(required=False, label='Papildomi numberiai iki')
    price = forms.CharField(required=False, max_length=10, label='Kaina')
    extra_price = forms.CharField(required=False, max_length=10, label='Papildoma kaina')
    extra_price_date = forms.DateField(required=False, label="Data nuo")
    if_race = forms.BooleanField(required=False, label='Estafetė?')
    race_participant_count = forms.IntegerField(required=False, label='Dalyvių skaičius')

