from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.conf import settings

from .recaptcha import verify_recaptcha_token
from .models import User


class LoginForm(AuthenticationForm):
    def clean(self):
        if getattr(settings, 'RECAPTCHA_ENABLED', False):
            token = self.data.get('g-recaptcha-response', '').strip()
            if not token:
                raise forms.ValidationError('Please complete the reCAPTCHA challenge.')

            remote_ip = None
            if self.request:
                forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if forwarded_for:
                    remote_ip = forwarded_for.split(',')[0].strip()
                else:
                    remote_ip = self.request.META.get('REMOTE_ADDR')

            is_valid, message = verify_recaptcha_token(token=token, remote_ip=remote_ip)
            if not is_valid:
                raise forms.ValidationError(message)

        return super().clean()


class SettingsUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = User.Role.AUDITOR

        placeholders = {
            'username': 'e.g., user001',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'user@example.mil',
            'password1': 'Create password',
            'password2': 'Confirm password',
        }
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]


class SettingsUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'e.g., user001',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'user@example.mil',
        }
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css} form-check-input'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]
