from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from operations.models import Aircraft


class MaintenanceLog(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='maintenance_logs')
    total_flight_hours = models.FloatField(validators=[MinValueValidator(0.0)])
    last_maintenance_date = models.DateField()
    component_status = models.CharField(max_length=128)
    maintenance_notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='maintenance_logs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Maintenance {self.aircraft.tail_number} @ {self.created_at:%Y-%m-%d}'


class Alert(models.Model):
    class Severity(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='alerts')
    maintenance_log = models.ForeignKey(MaintenanceLog, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=128)
    message = models.TextField()
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    is_resolved = models.BooleanField(default=False)
    recipient_role = models.CharField(max_length=32, default='maintenance')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.aircraft.tail_number} - {self.severity}'
