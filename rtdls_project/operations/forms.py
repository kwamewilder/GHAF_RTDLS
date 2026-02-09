from django import forms

from .models import Aircraft, Base, FlightLog, Pilot


class FlightLogForm(forms.ModelForm):
    altitude_ft = forms.FloatField(required=False, min_value=0, label='Altitude (ft)')
    speed_knots = forms.FloatField(required=False, min_value=0, label='Speed (knots)')
    atd = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        label='ATD',
    )
    eta = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        label='ETA',
    )
    ata = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=False,
        label='ATA',
    )

    class Meta:
        model = FlightLog
        fields = [
            'aircraft',
            'pilot',
            'crew_members',
            'mission_type',
            'atd',
            'eta',
            'ata',
            'flight_hours',
            'fuel_used',
            'departure_base',
            'arrival_base',
            'remarks',
            'altitude_ft',
            'speed_knots',
        ]
        widgets = {
            'crew_members': forms.SelectMultiple(attrs={'size': 5}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pilot'].queryset = Pilot.objects.filter(is_active=True).order_by('full_name')
        self.fields['aircraft'].empty_label = 'Select tail number'
        self.fields['pilot'].empty_label = 'Select pilot'
        self.fields['departure_base'].empty_label = 'Select departure base'
        self.fields['arrival_base'].empty_label = 'Select destination base'

        placeholders = {
            'aircraft': 'e.g., 9G AAA',
            'atd': 'Select actual departure',
            'eta': 'Select estimated arrival',
            'ata': 'Leave blank while flight is in progress',
            'mission_type': 'e.g., CASA C295',
            'altitude_ft': 'e.g., 35000',
            'speed_knots': 'e.g., 500',
            'flight_hours': 'e.g., 2.5',
            'fuel_used': 'e.g., 450',
            'remarks': 'Any additional notes or observations.',
        }
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            elif isinstance(field.widget, forms.HiddenInput):
                continue
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('departure_base') == cleaned_data.get('arrival_base'):
            self.add_error('arrival_base', 'Arrival base must be different from departure base.')
        if not cleaned_data.get('pilot'):
            self.add_error('pilot', 'Please select a pilot.')
        atd = cleaned_data.get('atd')
        eta = cleaned_data.get('eta')
        ata = cleaned_data.get('ata')
        if atd and eta and eta < atd:
            self.add_error('eta', 'ETA cannot be earlier than ATD.')
        if atd and ata and ata < atd:
            self.add_error('ata', 'ATA cannot be earlier than ATD.')
        return cleaned_data


class AircraftRegistryForm(forms.ModelForm):
    class Meta:
        model = Aircraft
        fields = ['tail_number', 'aircraft_type', 'model', 'home_base', 'maintenance_threshold_hours', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['home_base'].queryset = Base.objects.order_by('name')
        self.fields['home_base'].empty_label = 'Select home base'
        self.fields['status'].initial = Aircraft.Status.AVAILABLE

        placeholders = {
            'tail_number': 'e.g., 9G AAA',
            'aircraft_type': 'e.g., Transport',
            'model': 'e.g., CASA C295',
            'maintenance_threshold_hours': 'e.g., 100',
        }
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]

    def clean_tail_number(self):
        tail_number = self.cleaned_data['tail_number'].strip().upper()
        qs = Aircraft.objects.filter(tail_number__iexact=tail_number)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Aircraft with this tail number already exists.')
        return tail_number
