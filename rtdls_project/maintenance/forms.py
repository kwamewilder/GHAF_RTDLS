from django import forms

from .models import MaintenanceLog


class MaintenanceLogForm(forms.ModelForm):
    last_maintenance_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = MaintenanceLog
        fields = [
            'aircraft',
            'total_flight_hours',
            'last_maintenance_date',
            'component_status',
            'maintenance_notes',
        ]
        widgets = {
            'maintenance_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aircraft'].empty_label = 'Select aircraft'

        placeholders = {
            'total_flight_hours': 'e.g., 132.5',
            'component_status': 'e.g., Engine inspection required',
            'maintenance_notes': 'Record corrective actions, observations, and follow-up.',
        }

        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]
